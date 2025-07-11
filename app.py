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

# --- 1. Page Configuration ---
st.set_page_config(
    page_title="الصفحة الرئيسية | ماراثون القراءة",
    page_icon="📚",
    layout="wide"
)

# --- 2. Enhanced CSS Injection (Corrected for Streamlit Containers) ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap');
        
        /* --- Base & RTL --- */
        .stApp {
            direction: rtl;
            background-color: #f8f9fa;
        }
        [data-testid="stSidebar"] {
            direction: rtl;
        }
        h1, h2, h3, h4, h5, h6, p, li, label {
            text-align: right !important;
            font-family: 'Inter', sans-serif;
        }

        /* --- Main Title --- */
        .main-title {
            color: #2c3e50;
            font-weight: 700;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }

        /* --- Card Styling for st.container(border=True) --- */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: linear-gradient(135deg, #ffffff 0%, #fefefe 100%);
            border: 1px solid #e3e6ea !important;
            border-radius: 16px !important;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.06);
            transition: all 0.3s ease;
            position: relative;
            padding: 35px 25px 25px 25px !important; /* Added more top padding for the accent bar */
            margin-top: 20px;
            margin-bottom: 20px;
        }
        div[data-testid="stVerticalBlockBorderWrapper"]:hover {
            box-shadow: 0 12px 35px rgba(0, 0, 0, 0.1);
            transform: translateY(-3px);
            border-color: #667eea !important;
        }
        /* Accent Bar for the Card */
        div[data-testid="stVerticalBlockBorderWrapper"]::before {
            content: '';
            position: absolute;
            top: 0;
            right: 0;
            left: 0;
            height: 5px;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        }

        /* --- Enhanced Headers inside Cards --- */
        .enhanced-header {
            font-size: 1.6em;
            font-weight: 700;
            color: #2c3e50;
            margin-bottom: 20px;
            position: relative;
            padding-right: 20px;
        }
        .enhanced-header::before {
            content: '';
            position: absolute;
            right: 0;
            top: 50%;
            transform: translateY(-50%);
            width: 6px;
            height: 24px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 3px;
        }

        /* --- Custom List Styling --- */
        .custom-list ul { list-style: none; padding-right: 0; }
        .custom-list li {
            position: relative; padding-right: 25px; margin-bottom: 15px;
            font-size: 1.1em; color: #34495e; transition: all 0.2s ease;
        }
        .custom-list li:hover { color: #2c3e50; transform: translateX(-3px); }
        .custom-list li::before {
            content: '✓'; font-weight: bold; position: absolute; right: 0;
            top: 50%; transform: translateY(-50%); width: 20px; height: 20px;
            color: #667eea; font-size: 1.2em;
        }

        /* --- Sidebar Navigation Links --- */
        [data-testid="stSidebarNav"] ul { padding-right: 10px; }
        [data-testid="stSidebarNav"] a {
            font-size: 1.1em !important;
            padding: 10px 12px !important;
            margin-bottom: 5px;
            border-radius: 8px;
            transition: all 0.2s ease;
        }
        [data-testid="stSidebarNav"] a:hover {
            background-color: rgba(102, 126, 234, 0.1);
            color: #2c3e50;
            transform: translateX(-2px);
        }
        [data-testid="stSidebarNav"] a[aria-current="page"] {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white !important;
            font-weight: bold;
        }
    </style>
""", unsafe_allow_html=True)


# --- 3. Main App Authentication and Setup ---
creds = auth_manager.authenticate()
user_id = st.session_state.get('user_id')
user_email = st.session_state.get('user_email')

if not creds or not user_id:
    st.error("حدث خطأ في المصادقة. يرجى إعادة تحميل الصفحة.")
    st.stop()

# Initialize Google clients once and cache them
gc = auth_manager.get_gspread_client(user_id, creds)
forms_service = build('forms', 'v1', credentials=creds)

# --- 4. Sidebar ---
with st.sidebar:
    st.title("لوحة التحكم")
    st.success(f"أهلاً بك! {user_email}")

    if st.button("🚪 تسجيل الخروج", use_container_width=True):
        auth_manager.logout()

    st.divider()

    if st.button("🔄 تحديث وسحب البيانات", type="primary", use_container_width=True):
        with st.spinner("جاري سحب البيانات من Google Sheet الخاص بك..."):
            update_log = run_data_update(gc, user_id)
            st.session_state['update_log'] = update_log
        st.toast("اكتملت عملية المزامنة بنجاح!", icon="✅")

    if 'update_log' in st.session_state:
        st.info("اكتملت عملية المزامنة الأخيرة.")
        with st.expander("عرض تفاصيل سجل التحديث"):
            for message in st.session_state.update_log:
                st.text(message)
        del st.session_state['update_log']

# --- 5. Data Loading and Setup Check ---
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

# --- 6. Main Page Content ---
st.markdown('<h1 class="main-title">🚀 مرحباً بك في ماراثون القراءة!</h1>', unsafe_allow_html=True)

if not setup_complete:
    st.info("لتجهيز مساحة العمل الخاصة بك، يرجى اتباع الخطوات التالية:")
    
    # Step 1: Add Members
    if members_df.empty:
        with st.container(border=True):
            st.markdown('<h2 class="enhanced-header">الخطوة 1: إضافة أعضاء فريقك</h2>', unsafe_allow_html=True)
            st.warning("قبل المتابعة، يجب إضافة عضو واحد على الأقل.")
            with st.form("initial_members_form"):
                names_str = st.text_area("أدخل أسماء المشاركين (كل اسم في سطر جديد):", height=150, placeholder="خالد\nسارة\n...")
                if st.form_submit_button("إضافة الأعضاء وحفظهم", use_container_width=True, type="primary"):
                    names = [name.strip() for name in names_str.split('\n') if name.strip()]
                    if names:
                        with st.spinner("جاري إضافة الأعضاء..."):
                            db.add_members(user_id, names)
                        st.success("تمت إضافة الأعضاء بنجاح! سيتم تحديث الصفحة للمتابعة.")
                        st.balloons()
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error("يرجى إدخال اسم واحد على الأقل.")

    # Step 2: Create Google Tools
    elif not user_settings.get("spreadsheet_url") or not user_settings.get("form_url"):
        with st.container(border=True):
            st.markdown('<h2 class="enhanced-header">الخطوة 2: إنشاء أدوات جوجل</h2>', unsafe_allow_html=True)
            st.info("سيقوم التطبيق الآن بإنشاء جدول بيانات ونموذج تسجيل في حسابك.")
            if 'sheet_title' not in st.session_state:
                st.session_state.sheet_title = f"بيانات ماراثون القراءة - {user_email.split('@')[0]}"
            st.session_state.sheet_title = st.text_input("اختر اسماً لأدواتك:", value=st.session_state.sheet_title)

            if st.button("📝 إنشاء الشيت والفورم الآن", type="primary", use_container_width=True):
                # ... (Logic for creating sheet and form remains unchanged) ...
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
                        new_form_info = {"info": {"title": st.session_state.sheet_title, "documentTitle": st.session_state.sheet_title}}
                        form_result = forms_service.forms().create(body=new_form_info).execute()
                        form_id = form_result['formId']

                        update_requests = {"requests": [
                            {"updateFormInfo": {"info": {"description": "يرجى ملء هذا النموذج يومياً لتسجيل نشاطك في تحدي القراءة. بالتوفيق!"}, "updateMask": "description"}},
                            {"createItem": {"item": {"title": "اسمك", "questionItem": {"question": {"required": True, "choiceQuestion": {"type": "DROP_DOWN", "options": [{"value": name} for name in member_names]}}}}, "location": {"index": 0}}},
                            {"createItem": {"item": {"title": "تاريخ القراءة", "questionItem": {"question": {"required": True, "dateQuestion": {"includeTime": False, "includeYear": True}}}}, "location": {"index": 1}}},
                            {"createItem": {"item": {"title": "مدة قراءة الكتاب المشترك (اختياري)", "questionItem": {"question": {"timeQuestion": {"duration": True}}}}, "location": {"index": 2}}},
                            {"createItem": {"item": {"title": "مدة قراءة كتاب آخر (اختياري)", "questionItem": {"question": {"timeQuestion": {"duration": True}}}}, "location": {"index": 3}}},
                            {"createItem": {"item": {"title": "ما هي الاقتباسات التي أرسلتها اليوم؟ (اختياري)", "questionItem": {"question": {"choiceQuestion": {"type": "CHECKBOX", "options": [{"value": "أرسلت اقتباساً من الكتاب المشترك"}, {"value": "أرسلت اقتباساً من كتاب آخر"}]}}}}, "location": {"index": 4}}},
                            {"createItem": {"item": {"title": "إنجازات الكتب والنقاش (اختر فقط عند حدوثه لأول مرة)", "questionItem": {"question": {"choiceQuestion": {"type": "CHECKBOX", "options": [{"value": "أنهيت الكتاب المشترك"}, {"value": "أنهيت كتاباً آخر"}, {"value": "حضرت جلسة النقاش"}]}}}}, "location": {"index": 5}}}
                        ]}

                        update_result = forms_service.forms().batchUpdate(formId=form_id, body=update_requests).execute()
                        db.set_user_setting(user_id, "form_id", form_id)
                        db.set_user_setting(user_id, "form_url", form_result['responderUri'])
                        st.success("✅ تم إنشاء النموذج وحفظ إعداداته بنجاح!")
                    except Exception as e:
                        st.error(f"🌐 خطأ في إنشاء الفورم: {e}")
                        st.stop()

                st.markdown('<h3 class="enhanced-header" style="font-size: 1.3em; margin-top: 20px;">🔗 الخطوة الأخيرة: الربط والتحقق</h3>', unsafe_allow_html=True)
                st.warning("هذه الخطوات ضرورية جداً ويجب القيام بها مرة واحدة فقط.")
                editor_url = f"https://docs.google.com/forms/d/{form_id}/edit"

                st.write("1. **افتح النموذج للتعديل** من الرابط أدناه:")
                st.code(editor_url, language=None)
                st.write("2. انتقل إلى تبويب **\"الردود\" (Responses)**.")
                st.write("3. اضغط على أيقونة **'Link to Sheets'**.")
                st.write("4. اختر **'Select existing spreadsheet'** وقم باختيار جدول البيانات الذي أنشأته للتو.")
                st.write("5. **(هـام)** أعد تسمية ورقة الردود الجديدة إلى `Form Responses 1` بالضبط.")
                st.write("6. **(هـام)** افتح جدول البيانات، ومن القائمة العلوية اذهب إلى **File > Settings**، ثم غيّر الـ **Locale** إلى **United Kingdom** واضغط **Save settings**.")

                if st.button("تحقق من الإعدادات وتابع", type="primary", use_container_width=True):
                    # ... (Verification logic remains unchanged) ...
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
                            st.error("❌ فشل التحقق. لم يتم العثور على ورقة باسم 'Form Responses 1'. يرجى التأكد من إعادة تسميتها.")
                        except Exception as e:
                            st.error(f"حدث خطأ أثناء محاولة الوصول لجدول البيانات: {e}")

    # Step 3: Create First Challenge
    elif periods_df.empty:
        with st.container(border=True):
            st.markdown('<h2 class="enhanced-header">الخطوة 3: إنشاء أول تحدي لك</h2>', unsafe_allow_html=True)
            st.info("أنت على وشك الانتهاء! كل ما عليك فعله هو إضافة تفاصيل أول تحدي للبدء.")
            with st.form("new_challenge_form", clear_on_submit=True):
                st.text_input("عنوان الكتاب المشترك الأول", key="book_title")
                st.text_input("اسم المؤلف", key="book_author")
                st.number_input("سنة النشر", key="pub_year", value=date.today().year, step=1)
                st.date_input("تاريخ بداية التحدي", key="start_date", value=date.today())
                st.date_input("تاريخ نهاية التحدي", key="end_date", value=date.today() + timedelta(days=30))
                if st.form_submit_button("بدء التحدي الأول!", use_container_width=True, type="primary"):
                    # ... (Logic remains unchanged) ...
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

else:
    # --- MAIN WELCOME PAGE (if setup is complete) ---
    with st.container(border=True):
        st.success("🎉 اكتمل إعداد حسابك بنجاح! يمكنك الآن التنقل بين صفحات التطبيق المختلفة.")
        st.markdown('<h2 class="enhanced-header">ماذا يمكنك أن تفعل الآن؟</h2>', unsafe_allow_html=True)
        
        st.markdown("""
        <div class="custom-list">
            <ul>
                <li><b>📈 لوحة التحكم العامة:</b> للحصول على نظرة شاملة على أداء جميع المشاركين.</li>
                <li><b>🎯 تحليلات التحديات:</b> للغوص في تفاصيل تحدي معين ومقارنة أداء المشاركين فيه.</li>
                <li><b>⚙️ الإدارة والإعدادات:</b> لإضافة أعضاء جدد، إنشاء تحديات مستقبلية، أو تعديل نظام النقاط.</li>
                <li><b>❓ عن التطبيق:</b> لمعرفة المزيد عن المشروع وكيفية عمل نظام النقاط.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.info("🚀 **نصيحة:** ابدأ بالذهاب إلى **'لوحة التحكم العامة'** من الشريط الجانبي لرؤية الصورة الكاملة.")
