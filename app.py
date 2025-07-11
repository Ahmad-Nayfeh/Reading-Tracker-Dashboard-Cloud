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

# --- Page Configuration and RTL + Design CSS Injection ---
st.set_page_config(
    page_title="الصفحة الرئيسية | ماراثون القراءة",
    page_icon="📚",
    layout="wide"
)

st.markdown("""
    <style>
        /* RTL and text alignment */
        .stApp { direction: rtl; }
        [data-testid="stSidebar"] { direction: rtl; }
        h1, h2, h3, h4, h5, h6, p, li, .st-bk, .st-b8, .st-b9, .st-ae {
            text-align: right !important;
        }
        .st-b8 label, .st-ae label {
            text-align: right !important;
            display: block;
        }

        /* Modern Card Design */
        .card {
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            border: 1px solid #e3e6ea;
            border-radius: 16px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.06);
            transition: all 0.3s ease;
            position: relative;
            padding: 20px 25px;
            margin-bottom: 20px;
        }
        .card:hover {
            box-shadow: 0 12px 35px rgba(0, 0, 0, 0.1);
            transform: translateY(-2px);
        }
        .card::before {
            content: '';
            position: absolute;
            top: 0; right: 0; left: 0;
            height: 4px;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            border-radius: 16px 16px 0 0;
        }

        /* Enhanced Headers */
        .enhanced-header {
            font-size: 1.4em;
            font-weight: 700;
            color: #2c3e50;
            padding: 20px 25px;
            position: relative;
            margin: 0;
        }
        .enhanced-header::before {
            content: '';
            position: absolute;
            right: 25px;
            top: 50%;
            transform: translateY(-50%);
            width: 6px; height: 6px;
            background: #667eea;
            border-radius: 50%;
            box-shadow: 0 0 0 8px rgba(102, 126, 234, 0.1);
        }

        /* Custom Lists */
        .custom-list {
            list-style: none;
            padding-right: 0;
            margin: 0 0 20px 0;
        }
        .custom-list li {
            position: relative;
            padding-right: 25px;
            margin-bottom: 12px;
            transition: all 0.2s ease;
        }
        .custom-list li:hover {
            color: #2c3e50;
            transform: translateX(-3px);
        }
        .custom-list li::before {
            content: '';
            position: absolute;
            right: 0; top: 12px;
            width: 8px; height: 8px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 50%;
            box-shadow: 0 2px 4px rgba(102, 126, 234, 0.3);
        }

        /* Interactive Links */
        .interactive-link {
            text-decoration: none;
            color: #667eea;
            font-weight: 500;
            transition: all 0.3s ease;
            padding: 2px 8px;
            border-radius: 6px;
        }
        .interactive-link:hover {
            background: rgba(102, 126, 234, 0.1);
            color: #4c63d2;
            transform: translateX(-2px);
        }
    </style>
""", unsafe_allow_html=True)

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

# --- Data Retrieval ---
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
    # Step 1: Add Members
    if members_df.empty:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<h2 class="enhanced-header">الخطوة 1: إضافة أعضاء فريقك</h2>', unsafe_allow_html=True)
        st.warning("قبل المتابعة، يجب إضافة عضو واحد على الأقل.")
        with st.form("initial_members_form"):
            names_str = st.text_area("أدخل أسماء المشاركين (كل اسم في سطر جديد):", height=150, placeholder="خالد\nسارة\n...")
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

    # Step 2: Create Google Tools
    elif not user_settings.get("spreadsheet_url") or not user_settings.get("form_url"):
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<h2 class="enhanced-header">الخطوة 2: إنشاء أدوات جوجل</h2>', unsafe_allow_html=True)
        st.info("سيقوم التطبيق الآن بإنشاء جدول بيانات (Google Sheet) ونموذج تسجيل (Google Form) في حسابك.")
        if 'sheet_title' not in st.session_state:
            st.session_state.sheet_title = f"بيانات ماراثون القراءة - {user_email.split('@')[0]}"
        st.session_state.sheet_title = st.text_input("اختر اسماً لأدواتك (سيتم تطبيقه على الشيت والفورم):", value=st.session_state.sheet_title)

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
                        # ... بقية إعدادات الفورم كما في الأصل ...
                    ]}
                    update_result = forms_service.forms().batchUpdate(formId=form_id, body=update_requests).execute()
                    member_question_id = update_result['replies'][1]['createItem']['itemId']
                    db.set_user_setting(user_id, "form_id", form_id)
                    db.set_user_setting(user_id, "member_question_id", member_question_id)
                    db.set_user_setting(user_id, "form_url", form_result['responderUri'])
                    st.success("✅ تم إنشاء النموذج وحفظ إعداداته بنجاح!")
                except Exception as e:
                    st.error(f"🌐 خطأ في إنشاء الفورم: {e}")
                    st.stop()

            # تعليمات الربط والتحقق
            editor_url = f"https://docs.google.com/forms/d/{form_id}/edit"
            st.markdown("1. **افتح النموذج للتعديل** من الرابط أدناه:")
            st.markdown(f'<a href="{editor_url}" class="interactive-link" target="_blank">{editor_url}</a>', unsafe_allow_html=True)
            st.markdown("""
2. انتقل إلى تبويب **"الردود" (Responses)**  
3. اضغط على أيقونة **'Link to Sheets'**  
4. اختر **'Select existing spreadsheet'** وقم باختيار جدول البيانات بنفس الاسم  
5. أعد تسمية ورقة الردود إلى `Form Responses 1` بالضبط  
6. غير الـ **Locale** إلى **United Kingdom** من File > Settings  
""")
            if st.button("تحقق من الإعدادات وتابع", type="primary", use_container_width=True):
                with st.spinner("جاري التحقق من الإعدادات..."):
                    try:
                        spreadsheet = gc.open_by_url(user_settings.get("spreadsheet_url"))
                        worksheet = spreadsheet.worksheet("Form Responses 1")
                        st.success("✅ تم التحقق بنجاح! تم العثور على ورقة 'Form Responses 1'.")
                        try:
                            default_sheet = spreadsheet.worksheet('Sheet1')
                            spreadsheet.del_worksheet(default_sheet)
                            st.info("ℹ️ تم حذف ورقة 'Sheet1' الفارغة بنجاح.")
                        except gspread.exceptions.WorksheetNotFound:
                            pass
                        time.sleep(2)
                        st.rerun()
                    except gspread.exceptions.WorksheetNotFound:
                        st.error("❌ فشل التحقق. يرجى التأكد من إعادة التسمية إلى 'Form Responses 1'.")
                    except Exception as e:
                        st.error(f"حدث خطأ أثناء محاولة الوصول لجدول البيانات: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

    # Step 3: Create First Challenge
    elif periods_df.empty:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<h2 class="enhanced-header">الخطوة 3: إنشاء أول تحدي لك</h2>', unsafe_allow_html=True)
        st.info("أنت على وشك الانتهاء! كل ما عليك فعله هو إضافة تفاصيل أول كتاب وتحدي للبدء.")
        with st.form("new_challenge_form", clear_on_submit=True):
            st.text_input("عنوان الكتاب المشترك الأول", key="book_title")
            st.text_input("اسم المؤلف", key="book_author")
            st.number_input("سنة النشر", key="pub_year", value=date.today().year, step=1)
            st.date_input("تاريخ بداية التحدي", key="start_date", value=date.today())
            st.date_input("تاريخ نهاية التحدي", key="end_date", value=date.today() + timedelta(days=30))
            if st.form_submit_button("بدء التحدي الأول!", use_container_width=True, type="primary"):
                if st.session_state.book_title and st.session_state.book_author:
                    book_info = {'title': st.session_state.book_title, 'author': st.session_state.book_author, 'year': st.session_state.pub_year}
                    challenge_info = {'start_date': str(st.session_state.start_date), 'end_date': str(st.session_state.end_date)}
                    default_rules = db.load_user_global_rules(user_id)
                    if default_rules:
                        success, message = db.add_book_and_challenge(user_id, book_info, challenge_info, default_rules)
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
    # --- MAIN WELCOME PAGE ---
    st.markdown('<h3 class="enhanced-header">📚 أهلاً بك في لوحة تحكم ماراثون القراءة</h3>', unsafe_allow_html=True)
    st.markdown("---")
    st.info("🎉 اكتمل إعداد حسابك بنجاح!")

    st.markdown('<h3 class="enhanced-header">ماذا يمكنك أن تفعل الآن؟</h3>', unsafe_allow_html=True)
    st.markdown("""
<ul class="custom-list">
<li><strong>📈 لوحة التحكم العامة:</strong> للحصول على نظرة شاملة على أداء جميع المشاركين في كل التحديات.</li>
<li><strong>🎯 تحليلات التحديات:</strong> للغوص في تفاصيل تحدي معين ومقارنة أداء المشاركين فيه.</li>
<li><strong>⚙️ الإدارة والإعدادات:</strong> لإضافة أعضاء جدد، إنشاء تحديات مستقبلية، أو تعديل نظام النقاط.</li>
<li><strong>❓ عن التطبيق:</strong> لمعرفة المزيد عن المشروع وكيفية عمل نظام النقاط.</li>
</ul>
""", unsafe_allow_html=True)

    st.success("🚀 **نصيحة:** ابدأ بالذهاب إلى **'Overall Dashboard'** من الشريط الجانبي لرؤية الصورة الكاملة.")
