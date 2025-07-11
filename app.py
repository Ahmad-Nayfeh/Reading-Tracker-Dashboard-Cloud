# الكود المعدّل: app.py
import streamlit as st
import pandas as pd
from datetime import date, timedelta, datetime
import db_manager as db
from main import run_data_update
import auth_manager
from googleapiclient.discovery import build
import gspread
import time
import os

# --- Page Configuration and RTL CSS Injection ---
st.set_page_config(
    page_title="الصفحة الرئيسية | ماراثون القراءة",
    page_icon="📚",
    layout="wide"
)

# Inject CSS for RTL and Modern Design
st.markdown("""
    <style>
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
            padding: 20px 25px;
            margin-bottom: 20px;
            transition: all 0.3s ease;
            position: relative;
        }

        .card:hover {
            box-shadow: 0 12px 35px rgba(0, 0, 0, 0.1);
            transform: translateY(-2px);
        }

        .card::before {
            content: '';
            position: absolute;
            top: 0;
            right: 0;
            left: 0;
            height: 4px;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            border-radius: 16px 16px 0 0;
        }

        .enhanced-header {
            font-size: 1.4em;
            font-weight: 700;
            color: #2c3e50;
            padding: 10px 0;
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
    </style>
""", unsafe_allow_html=True)

# --- Main App Authentication and Setup ---
creds = auth_manager.authenticate()
user_id = st.session_state.get('user_id')
user_email = st.session_state.get('user_email')

if not creds or not user_id:
    st.error("حدث خطأ في المصادقة. يرجى إعادة تحميل الصفحة.")
    st.stop()

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

# --- Check Setup ---
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

# --- Main Page ---
if not setup_complete:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="enhanced-header">🚀 مرحباً بك في ماراثون القراءة!</div>', unsafe_allow_html=True)
    st.info("لتجهيز مساحة العمل الخاصة بك، يرجى اتباع الخطوات التالية:")

    if members_df.empty:
        st.markdown('<div class="enhanced-header">الخطوة 1: إضافة أعضاء فريقك</div>', unsafe_allow_html=True)
        st.warning("قبل المتابعة، يجب إضافة عضو واحد على الأقل.")
        with st.form("initial_members_form"):
            names_str = st.text_area("أدخل أسماء المشاركين (كل اسم في سطر جديد):", height=150, placeholder="خالد\nسارة\n...")
            if st.form_submit_button("إضافة الأعضاء وحفظهم", use_container_width=True, type="primary"):
                names = [name.strip() for name in names_str.split('\n') if name.strip()]
                if names:
                    with st.spinner("جاري إضافة الأعضاء..."):
                        db.add_members(user_id, names)
                    st.success("تمت إضافة الأعضاء بنجاح!")
                    st.balloons()
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("يرجى إدخال اسم واحد على الأقل.")
        st.markdown('</div>', unsafe_allow_html=True)

    elif not user_settings.get("spreadsheet_url") or not user_settings.get("form_url"):
        st.markdown('<div class="enhanced-header">الخطوة 2: إنشاء أدوات جوجل</div>', unsafe_allow_html=True)
        st.info("سيقوم التطبيق بإنشاء جدول بيانات ونموذج تسجيل في حسابك.")
        if 'sheet_title' not in st.session_state:
            st.session_state.sheet_title = f"بيانات ماراثون القراءة - {user_email.split('@')[0]}"
        st.session_state.sheet_title = st.text_input("اختر اسماً لأدواتك:", value=st.session_state.sheet_title)

        if st.button("📝 إنشاء الشيت والفورم الآن", type="primary", use_container_width=True):
            with st.spinner("جاري الإنشاء..."):
                try:
                    spreadsheet = gc.create(st.session_state.sheet_title)
                    db.set_user_setting(user_id, "spreadsheet_url", spreadsheet.url)
                    st.success("✅ تم إنشاء جدول البيانات.")
                except Exception as e:
                    st.error(f"خطأ في الشيت: {e}")
                    st.stop()

            with st.spinner("جاري إنشاء النموذج..."):
                try:
                    member_names = members_df['name'].tolist()
                    new_form_info = {"info": {"title": st.session_state.sheet_title, "documentTitle": st.session_state.sheet_title}}
                    form_result = forms_service.forms().create(body=new_form_info).execute()
                    form_id = form_result['formId']

                    update_requests = {"requests": [
                        {"updateFormInfo": {"info": {"description": "يرجى ملء هذا النموذج يومياً..."}, "updateMask": "description"}},
                        {"createItem": {"item": {"title": "اسمك", "questionItem": {"question": {"required": True, "choiceQuestion": {"type": "DROP_DOWN", "options": [{"value": name} for name in member_names]}}}}, "location": {"index": 0}}},
                        {"createItem": {"item": {"title": "تاريخ القراءة", "questionItem": {"question": {"required": True, "dateQuestion": {"includeTime": False, "includeYear": True}}}}, "location": {"index": 1}}},
                        {"createItem": {"item": {"title": "مدة قراءة الكتاب المشترك (اختياري)", "questionItem": {"question": {"timeQuestion": {"duration": True}}}}, "location": {"index": 2}}},
                        {"createItem": {"item": {"title": "مدة قراءة كتاب آخر (اختياري)", "questionItem": {"question": {"timeQuestion": {"duration": True}}}}, "location": {"index": 3}}},
                        {"createItem": {"item": {"title": "الاقتباسات", "questionItem": {"question": {"choiceQuestion": {"type": "CHECKBOX", "options": [{"value": "اقتباس من الكتاب"}, {"value": "اقتباس آخر"}]}}}}, "location": {"index": 4}}},
                        {"createItem": {"item": {"title": "الإنجازات", "questionItem": {"question": {"choiceQuestion": {"type": "CHECKBOX", "options": [{"value": "أنهيت الكتاب"}, {"value": "حضرت جلسة"}]}}}}, "location": {"index": 5}}}
                    ]}
                    update_result = forms_service.forms().batchUpdate(formId=form_id, body=update_requests).execute()
                    member_question_id = update_result['replies'][1]['createItem']['itemId']
                    db.set_user_setting(user_id, "form_id", form_id)
                    db.set_user_setting(user_id, "member_question_id", member_question_id)
                    db.set_user_setting(user_id, "form_url", form_result['responderUri'])
                    st.success("✅ النموذج جاهز!")
                except Exception as e:
                    st.error(f"خطأ في الفورم: {e}")
                    st.stop()

        st.markdown('</div>', unsafe_allow_html=True)

    elif periods_df.empty:
        st.markdown('<div class="enhanced-header">الخطوة 3: إنشاء أول تحدي</div>', unsafe_allow_html=True)
        st.info("أضف تفاصيل أول كتاب لبدء التحدي.")
        with st.form("new_challenge_form", clear_on_submit=True):
            st.text_input("عنوان الكتاب", key="book_title")
            st.text_input("اسم المؤلف", key="book_author")
            st.number_input("سنة النشر", key="pub_year", value=date.today().year)
            st.date_input("تاريخ البداية", key="start_date", value=date.today())
            st.date_input("تاريخ النهاية", key="end_date", value=date.today() + timedelta(days=30))
            if st.form_submit_button("بدء التحدي!", use_container_width=True, type="primary"):
                if st.session_state.book_title and st.session_state.book_author:
                    book_info = {'title': st.session_state.book_title, 'author': st.session_state.book_author, 'year': st.session_state.pub_year}
                    challenge_info = {'start_date': str(st.session_state.start_date), 'end_date': str(st.session_state.end_date)}
                    default_rules = db.load_user_global_rules(user_id)
                    if default_rules:
                        success, message = db.add_book_and_challenge(user_id, book_info, challenge_info, default_rules)
                        if success:
                            st.success("🎉 تم إنشاء أول تحدي!")
                            st.balloons()
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error(f"خطأ: {message}")
                    else:
                        st.error("لم يتم العثور على الإعدادات الافتراضية.")
                else:
                    st.error("يرجى إدخال عنوان واسم المؤلف.")

else:
    st.title("📚 أهلاً بك في لوحة تحكم ماراثون القراءة")
    st.markdown("---")
    st.info("🎉 اكتمل الإعداد! يمكنك التنقل في الشريط الجانبي.")
    st.subheader("ماذا يمكنك أن تفعل الآن؟")
    st.markdown("""
    - **📈 لوحة التحكم العامة:** نظرة شاملة على الأداء.
    - **🎯 تحليلات التحديات:** تفاصيل كل تحدي.
    - **⚙️ الإدارة والإعدادات:** إضافة أو تعديل الأعضاء والتحديات.
    - **❓ عن التطبيق:** مزيد من المعلومات حول المشروع.
    """)
    st.success("🚀 **نصيحة:** ابدأ بـ 'Overall Dashboard' لرؤية الصورة الكاملة.")
