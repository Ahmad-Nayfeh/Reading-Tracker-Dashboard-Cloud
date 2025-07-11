import streamlit as st
import pandas as pd
from datetime import date, timedelta, datetime
import db_manager as db
from main import run_data_update
import auth_manager
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import gspread
import time
import os

# --- Page Configuration and RTL CSS Injection ---
st.set_page_config(
    page_title="الصفحة الرئيسية | ماراثون القراءة",
    page_icon="📚",
    layout="wide"
)

# RTL baseline (كما في الملف الأصلي)
st.markdown("""
    <style>
        /* Main app container */
        .stApp {
            direction: rtl;
        }
        /* Sidebar */
        [data-testid="stSidebar"] {
            direction: rtl;
        }
        /* Ensure text alignment is right for various elements */
        h1, h2, h3, h4, h5, h6, p, li, .st-bk, .st-b8, .st-b9, .st-ae {
            text-align: right !important;
        }
        /* Fix for radio buttons label alignment */
        .st-b8 label {
            text-align: right !important;
            display: block;
        }
        /* Fix for selectbox label alignment */
        .st-ae label {
            text-align: right !important;
            display: block;
        }
    </style>
""", unsafe_allow_html=True)

# --- Modern Card Design CSS (إضافة جديدة) ---
additional_css = """
<style>
/* ===== Modern Card Design with Elevated Shadows ===== */

/* 1. Elevated Card */
.card {
    background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
    border: 1px solid #e3e6ea;
    border-radius: 16px;
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.06);
    transition: all 0.3s ease;
    position: relative;
    padding: 20px 25px;
    margin: 12px 0;
}
.card:hover {
    box-shadow: 0 12px 35px rgba(0, 0, 0, 0.10);
    transform: translateY(-2px);
}
/* Accent line */
.card::before {
    content: '';
    position: absolute;
    top: 0; right: 0; left: 0;
    height: 4px;
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    border-radius: 16px 16px 0 0;
}

/* 2. Enhanced Header */
.enhanced-header {
    font-size: 1.4em;
    font-weight: 700;
    color: #2c3e50;
    padding-bottom: 15px;
    position: relative;
}
.enhanced-header::before {
    content: '';
    position: absolute;
    right: 0;
    top: 50%;
    transform: translateY(-50%);
    width: 6px;
    height: 6px;
    background: #667eea;
    border-radius: 50%;
    box-shadow: 0 0 0 8px rgba(102, 126, 234, 0.1);
}

/* 3. Sidebar buttons subtle motion */
section[data-testid="stSidebar"] button {
    border-radius: 6px !important;
    transition: all 0.3s ease !important;
}
section[data-testid="stSidebar"] button:hover {
    transform: translateX(-3px) !important;
}

/* 4. Give Streamlit alerts a soft card look */
[data-testid="stAlert"] {
    border-radius: 16px !important;
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.06) !important;
}

/* 5. Smooth transitions for interactive elements */
button, input, select, textarea, .st-b8, .st-b9 {
    transition: all 0.3s ease;
}
</style>
"""
st.markdown(additional_css, unsafe_allow_html=True)

# --- Main App Authentication and Setup ---
creds = auth_manager.authenticate()

user_id = st.session_state.get('user_id')
user_email = st.session_state.get('user_email')

if not creds or not user_id:
    st.error("حدث خطأ في المصادقة. يرجى إعادة تحميل الصفحة.")
    st.stop()

# Initialize Google clients once and cache them
gc = auth_manager.get_gspread_client(user_id, creds)
forms_service = build('forms', 'v1', credentials=creds)

# --- Sidebar ---
st.sidebar.title("لوحة التحكم")
st.sidebar.success(f"أهلاً بك! {user_email}")

# Add the logout button
if st.sidebar.button("🚪 تسجيل الخروج", use_container_width=True):
    auth_manager.logout()

st.sidebar.divider()

if st.sidebar.button("🔄 تحديث وسحب البيانات", type="primary", use_container_width=True):
    with st.spinner("جاري سحب البيانات من Google Sheet الخاص بك..."):
        update_log = run_data_update(gc, user_id)
        st.session_state['update_log'] = update_log
    st.toast("اكتملت عملية المزامنة بنجاح!", icon="✅")


if 'update_log' in st.session_state:
    st.sidebar.info("اكتملت عملية المزامنة الأخيرة.")
    with st.sidebar.expander("عرض تفاصيل سجل التحديث"):
        for message in st.session_state.update_log:
            st.text(message)
    del st.session_state['update_log']


# --- Check if setup is complete ---
user_settings = db.get_user_settings(user_id)
all_data = db.get_all_data_for_stats(user_id)
members_df = pd.DataFrame(all_data.get('members', []))
periods_df = pd.DataFrame(all_data.get('periods', []))

setup_complete = (
    user_settings.get("spreadsheet_url") and
    user_settings.get("form_url") and
    not members_df.empty and
    not periods_df.empty
)

# --- Main Page Content ---
if not setup_complete:
    # --- SETUP WIZARD ---
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.title("🚀 مرحباً بك في ماراثون القراءة!")
    st.info("لتجهيز مساحة العمل الخاصة بك، يرجى اتباع الخطوات التالية:")
    st.markdown('</div>', unsafe_allow_html=True)

    # Step 1: Add Members
    if members_df.empty:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.header("الخطوة 1: إضافة أعضاء فريقك")
        st.warning("قبل المتابعة، يجب إضافة عضو واحد على الأقل.")
        with st.form("initial_members_form"):
            names_str = st.text_area("أدخل أسماء المشاركين (كل اسم في سطر جديد):", height=150,
                                     placeholder="خالد\nسارة\n...")
            if st.form_submit_button("إضافة الأعضاء وحفظهم", use_container_width=True, type="primary"):
                names = [name.strip() for name in names_str.split('\n') if name.strip()]
                if names:
                    with st.spinner("جاري إضافة الأعضاء..."):
                        db.add_members(user_id, names)
                    st.success("تمت إضافة الأعضاء بنجاح! سيتم تحديث الصفحة للمتابعة إلى الخطوة التالية.")
                    st.balloons()
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("يرجى إدخال اسم واحد على الأقل.")
        st.markdown('</div>', unsafe_allow_html=True)

    # Step 2: Create Google Tools
    elif not user_settings.get("spreadsheet_url") or not user_settings.get("form_url"):
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.header("الخطوة 2: إنشاء أدوات جوجل")
        st.info("سيقوم التطبيق الآن بإنشاء جدول بيانات (Google Sheet) ونموذج تسجيل (Google Form) في حسابك.")
        if 'sheet_title' not in st.session_state:
            st.session_state.sheet_title = f"بيانات ماراثون القراءة - {user_email.split('@')[0]}"
        st.session_state.sheet_title = st.text_input("اختر اسماً لأدواتك (سيتم تطبيقه على الشيت والفورم):",
                                                     value=st.session_state.sheet_title)

        if st.button("📝 إنشاء الشيت والفورم الآن", type="primary", use_container_width=True):
            with st.spinner("جاري إنشاء جدول البيانات..."):
                try:
                    spreadsheet = gc.create(st.session_state.sheet_title)
                    db.set_user_setting(user_id, "spreadsheet_url", spreadsheet.url)
                    st.success("✅ تم إنشاء جدول البيانات بنجاح!")
                except Exception as e:
                    st.error(f"🌐 خطأ في إنشاء الشيت: {e}")
                    st.stop()

            with st.spinner("جاري إنشاء نموذج التسجيل..."):
                try:
                    member_names = members_df['name'].tolist()
                    new_form_info = {
                        "info": {
                            "title": st.session_state.sheet_title,
                            "documentTitle": st.session_state.sheet_title
                        }
                    }
                    form_result = forms_service.forms().create(body=new_form_info).execute()
                    form_id = form_result['formId']

                    update_requests = {"requests": [
                        {"updateFormInfo": {"info": {"description": "يرجى ملء هذا النموذج يومياً لتسجيل نشاطك في تحدي القراءة. بالتوفيق!"},
                                            "updateMask": "description"}},
                        {"createItem": {"item": {"title": "اسمك",
                                                 "questionItem": {"question": {"required": True,
                                                                               "choiceQuestion": {"type": "DROP_DOWN",
                                                                                                  "options": [{"value": name}
                                                                                                              for name in member_names]}}}},
                                        "location": {"index": 0}}},
                        {"createItem": {"item": {"title": "تاريخ القراءة",
                                                 "questionItem": {"question": {"required": True,
                                                                               "dateQuestion": {"includeTime": False,
                                                                                                "includeYear": True}}}},
                                        "location": {"index": 1}}},
                        {"createItem": {"item": {"title": "مدة قراءة الكتاب المشترك (اختياري)",
                                                 "questionItem": {"question": {"timeQuestion": {"duration": True}}}},
                                        "location": {"index": 2}}},
                        {"createItem": {"item": {"title": "مدة قراءة كتاب آخر (اختياري)",
                                                 "questionItem": {"question": {"timeQuestion": {"duration": True}}}},
                                        "location": {"index": 3}}},
                        {"createItem": {"item": {"title": "ما هي الاقتباسات التي أرسلتها اليوم؟ (اختياري)",
                                                 "questionItem": {"question": {"choiceQuestion": {"type": "CHECKBOX",
                                                                                                 "options": [{"value": "أرسلت اقتباساً من الكتاب المشترك"},
                                                                                                             {"value": "أرسلت اقتباساً من كتاب آخر"}]}}}},
                                        "location": {"index": 4}}},
                        {"createItem": {"item": {"title": "إنجازات الكتب والنقاش (اختر فقط عند حدوثه لأول مرة)",
                                                 "questionItem": {"question": {"choiceQuestion": {"type": "CHECKBOX",
                                                                                                 "options": [{"value": "أنهيت الكتاب المشترك"},
                                                                                                             {"value": "أنهيت كتاباً آخر"},
                                                                                                             {"value": "حضرت جلسة النقاش"}]}}}},
                                        "location": {"index": 5}}}
                    ]}

                    update_result = forms_service.forms().batchUpdate(formId=form_id,
                                                                      body=update_requests).execute()

                    member_question_id = update_result['replies'][1]['createItem']['itemId']
                    db.set_user_setting(user_id, "form_id", form_id)
                    db.set_user_setting(user_id, "member_question_id", member_question_id)
                    db.set_user_setting(user_id, "form_url", form_result['responderUri'])

                    st.success("✅ تم إنشاء النموذج وحفظ إعداداته بنجاح!")
                except Exception as e:
                    st.error(f"🌐 خطأ في إنشاء الفورم: {e}")
                    st.stop()

            st.header("🔗 الخطوة الأخيرة: الربط والتحقق")
            st.warning("هذه الخطوات ضرورية جداً ويجب القيام بها مرة واحدة فقط.")
            editor_url = f"https://docs.google.com/forms/d/{form_id}/edit"

            st.write("1. **افتح النموذج للتعديل** من الرابط أدناه:")
            st.code(editor_url)
            st.write("2. انتقل إلى تبويب **\"الردود\" (Responses)**.")
            st.write("3. اضغط على أيقونة **'Link to Sheets'** (أيقونة جدول البيانات الخضراء).")
            st.write("4. اختر **'Select existing spreadsheet'** وقم باختيار جدول البيانات الذي أنشأته للتو بنفس الاسم.")
            st.write("5. **(خطوة هامة جداً)** سيتم إنشاء ورقة عمل جديدة. اضغط عليها وقم **بإعادة تسميتها** إلى `Form Responses 1` بالضبط.")
            st.write("6. **(للتواريخ)** افتح جدول البيانات، ومن القائمة العلوية اذهب إلى **File > Settings**، ثم غيّر الـ **Locale** إلى **United Kingdom** واضغط **Save settings**.")

            if st.button("تحقق من الإعدادات وتابع", type="primary", use_container_width=True):
                with st.spinner("جاري التحقق من الإعدادات..."):
                    try:
                        spreadsheet = gc.open_by_url(user_settings.get("spreadsheet_url"))
                        worksheet = spreadsheet.worksheet("Form Responses 1")
                        st.success("✅ تم التحقق بنجاح! تم العثور على ورقة 'Form Responses 1'.")
                        # Delete default empty sheet if exists
                        try:
                            default_sheet = spreadsheet.worksheet('Sheet1')
                            spreadsheet.del_worksheet(default_sheet)
                            st.info("ℹ️ تم حذف ورقة 'Sheet1' الفارغة بنجاح.")
                        except gspread.exceptions.WorksheetNotFound:
                            pass
                        time.sleep(2)
                        st.rerun()
                    except gspread.exceptions.WorksheetNotFound:
                        st.error("❌ فشل التحقق. لم نتمكن من العثور على ورقة باسم 'Form Responses 1'. يرجى التأكد من أنك قمت بإعادة تسمية ورقة الردود إلى هذا الاسم بالضبط.")
                    except Exception as e:
                        st.error(f"حدث خطأ أثناء محاولة الوصول لجدول البيانات: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

    # Step 3: Create First Challenge
    elif periods_df.empty:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.header("الخطوة 3: إنشاء أول تحدي لك")
        st.info("أنت على وشك الانتهاء! كل ما عليك فعله هو إضافة تفاصيل أول كتاب وتحدي للبدء.")
        with st.form("new_challenge_form", clear_on_submit=True):
            st.text_input("عنوان الكتاب المشترك الأول", key="book_title")
            st.text_input("اسم المؤلف", key="book_author")
            st.number_input("سنة النشر", key="pub_year", value=date.today().year, step=1)
            st.date_input("تاريخ بداية التحدي", key="start_date", value=date.today())
            st.date_input("تاريخ نهاية التحدي", key="end_date", value=date.today() + timedelta(days=30))
            if st.form_submit_button("بدء التحدي الأول!", use_container_width=True, type="primary"):
                if st.session_state.book_title and st.session_state.book_author:
                    book_info = {
                        'title': st.session_state.book_title,
                        'author': st.session_state.book_author,
                        'year': st.session_state.pub_year
                    }
                    challenge_info = {
                        'start_date': str(st.session_state.start_date),
                        'end_date': str(st.session_state.end_date)
                    }
                    default_rules = db.load_user_global_rules(user_id)
                    if default_rules:
                        success, message = db.add_book_and_challenge(user_id,
                                                                     book_info,
                                                                     challenge_info,
                                                                     default_rules)
                        if success:
                            st.success("🎉 اكتمل الإعداد! تم إنشاء أول تحدي بنجاح.")
                            st.balloons()
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error(f"❌ فشلت العملية: {message}")
                    else:
                        st.error("لم يتم العثور على الإعدادات الافتراضية في قاعدة البيانات.")
                else:
                    st.error("✏️ بيانات غير مكتملة: يرجى إدخال عنوان الكتاب واسم المؤلف.")
        st.markdown('</div>', unsafe_allow_html=True)

else:
    # --- MAIN WELCOME PAGE (if setup is complete) ---
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.title("📚 أهلاً بك في لوحة تحكم ماراثون القراءة")
    st.markdown("---")
    st.info("🎉 اكتمل إعداد حسابك بنجاح!")
    st.markdown("يمكنك الآن التنقل بين صفحات التطبيق المختلفة باستخدام القائمة الموجودة في الشريط الجانبي.")

    st.subheader("ماذا يمكنك أن تفعل الآن؟", anchor=None)
    st.markdown("""
    - **📈 لوحة التحكم العامة:** للحصول على نظرة شاملة على أداء جميع المشاركين في كل التحديات.  
    - **🎯 تحليلات التحديات:** للغوص في تفاصيل تحدي معين ومقارنة أداء المشاركين فيه.  
    - **⚙️ الإدارة والإعدادات:** لإضافة أعضاء جدد، إنشاء تحديات مستقبلية، أو تعديل نظام النقاط.  
    - **❓ عن التطبيق:** لمعرفة المزيد عن المشروع وكيفية عمل نظام النقاط.  
    """)
    st.success("🚀 **نصيحة:** ابدأ بالذهاب إلى **'Overall Dashboard'** من الشريط الجانبي لرؤية الصورة الكاملة.")
    st.markdown('</div>', unsafe_allow_html=True)
