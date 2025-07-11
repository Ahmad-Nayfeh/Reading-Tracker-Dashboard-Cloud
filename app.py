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

# Enhanced CSS for beautiful RTL layout
st.markdown("""
    <style>
        /* Main app container */
        .stApp {
            direction: rtl;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            background-attachment: fixed;
        }
        
        /* Main content area */
        .main .block-container {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            padding: 2rem;
            margin: 1rem;
        }
        
        /* Sidebar styling */
        [data-testid="stSidebar"] {
            direction: rtl;
            background: linear-gradient(180deg, #4facfe 0%, #00f2fe 100%);
            border-radius: 0 20px 20px 0;
        }
        
        [data-testid="stSidebar"] .block-container {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            margin: 1rem 0.5rem;
            padding: 1rem;
            backdrop-filter: blur(5px);
        }
        
        /* Headers styling */
        h1 {
            text-align: right !important;
            color: #2c3e50;
            font-weight: 700;
            margin-bottom: 1.5rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        }
        
        h2, h3 {
            text-align: right !important;
            color: #34495e;
            font-weight: 600;
            margin: 1.5rem 0 1rem 0;
        }
        
        /* Text elements */
        p, li, .st-bk, .st-b8, .st-b9, .st-ae {
            text-align: right !important;
            color: #2c3e50;
        }
        
        /* Form elements */
        .st-b8 label, .st-ae label {
            text-align: right !important;
            display: block;
            font-weight: 600;
            color: #34495e;
        }
        
        /* Buttons enhancement */
        .stButton > button {
            background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 0.75rem 2rem;
            font-weight: 600;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            transition: all 0.3s ease;
            text-align: center;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
        }
        
        /* Primary button styling */
        .stButton > button[kind="primary"] {
            background: linear-gradient(45deg, #ff6b6b 0%, #ee5a24 100%);
            box-shadow: 0 4px 15px rgba(255, 107, 107, 0.4);
        }
        
        .stButton > button[kind="primary"]:hover {
            box-shadow: 0 6px 20px rgba(255, 107, 107, 0.6);
        }
        
        /* Success/Info/Warning boxes */
        .stAlert {
            border-radius: 12px;
            border: none;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
        }
        
        .stSuccess {
            background: linear-gradient(45deg, #00b894 0%, #00a085 100%);
            color: white;
        }
        
        .stInfo {
            background: linear-gradient(45deg, #74b9ff 0%, #0984e3 100%);
            color: white;
        }
        
        .stWarning {
            background: linear-gradient(45deg, #fdcb6e 0%, #e17055 100%);
            color: white;
        }
        
        .stError {
            background: linear-gradient(45deg, #fd79a8 0%, #e84393 100%);
            color: white;
        }
        
        /* Form styling */
        .stForm {
            background: rgba(255, 255, 255, 0.8);
            border-radius: 15px;
            padding: 2rem;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.3);
        }
        
        /* Input fields */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stNumberInput > div > div > input,
        .stDateInput > div > div > input {
            border-radius: 10px;
            border: 2px solid #ddd;
            transition: all 0.3s ease;
        }
        
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus,
        .stNumberInput > div > div > input:focus,
        .stDateInput > div > div > input:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        /* Divider styling */
        hr {
            border: none;
            height: 2px;
            background: linear-gradient(90deg, transparent, #667eea, transparent);
            margin: 2rem 0;
        }
        
        /* Expander styling */
        .streamlit-expanderHeader {
            background: rgba(102, 126, 234, 0.1);
            border-radius: 10px;
            padding: 0.5rem;
        }
        
        /* Code blocks */
        .stCode {
            background: rgba(44, 62, 80, 0.1);
            border-radius: 10px;
            border: 1px solid rgba(102, 126, 234, 0.2);
        }
        
        /* Animations */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .main .block-container {
            animation: fadeIn 0.6s ease-out;
        }
        
        /* Welcome icons */
        .welcome-icon {
            font-size: 3rem;
            text-align: center;
            margin: 1rem 0;
            display: block;
        }
        
        /* Step indicators */
        .step-indicator {
            display: inline-block;
            background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 50px;
            font-weight: 600;
            margin-bottom: 1rem;
            box-shadow: 0 2px 10px rgba(102, 126, 234, 0.3);
        }
        
        /* Feature cards */
        .feature-card {
            background: rgba(255, 255, 255, 0.9);
            border-radius: 15px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            border-left: 4px solid #667eea;
            transition: all 0.3s ease;
        }
        
        .feature-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
        }
    </style>
""", unsafe_allow_html=True)

# --- Main App Authentication and Setup ---
creds = auth_manager.authenticate()

user_id = st.session_state.get('user_id')
user_email = st.session_state.get('user_email')

if not creds or not user_id:
    st.error("🔐 حدث خطأ في المصادقة. يرجى إعادة تحميل الصفحة.")
    st.stop()

# Initialize Google clients once and cache them
gc = auth_manager.get_gspread_client(user_id, creds)
forms_service = build('forms', 'v1', credentials=creds)

# --- Enhanced Sidebar ---
with st.sidebar:
    st.markdown('<div class="welcome-icon">🎯</div>', unsafe_allow_html=True)
    st.title("لوحة التحكم")
    st.markdown("---")
    st.success(f"✨ أهلاً بك، {user_email.split('@')[0]}!")
    
    st.markdown("---")
    
    # Enhanced update button
    if st.button("🔄 تحديث وسحب البيانات", type="primary", use_container_width=True):
        with st.spinner("✨ جاري سحب البيانات من Google Sheet الخاص بك..."):
            update_log = run_data_update(gc, user_id)
            st.session_state['update_log'] = update_log
        st.toast("🎉 اكتملت عملية المزامنة بنجاح!", icon="✅")

    # Update log display
    if 'update_log' in st.session_state:
        st.info("✅ اكتملت عملية المزامنة الأخيرة.")
        with st.expander("📋 عرض تفاصيل سجل التحديث"):
            for message in st.session_state.update_log:
                st.text(message)
        del st.session_state['update_log']
    
    st.markdown("---")
    
    # Enhanced logout button
    if st.button("🚪 تسجيل الخروج", use_container_width=True):
        auth_manager.logout()

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
    # --- ENHANCED SETUP WIZARD ---
    st.markdown('<div class="welcome-icon">🚀</div>', unsafe_allow_html=True)
    st.title("مرحباً بك في ماراثون القراءة!")
    st.markdown("---")
    
    st.markdown("""
    <div class="feature-card">
        <h3>🌟 لتجهيز مساحة العمل الخاصة بك</h3>
        <p>سنقوم معاً بإعداد كل ما تحتاجه للبدء في رحلة القراءة الرائعة هذه!</p>
    </div>
    """, unsafe_allow_html=True)

    # Step 1: Add Members
    if members_df.empty:
        st.markdown('<div class="step-indicator">الخطوة 1 من 3</div>', unsafe_allow_html=True)
        st.header("👥 إضافة أعضاء فريقك")
        
        st.markdown("""
        <div class="feature-card">
            <h4>🎯 لنبدأ بإضافة الأعضاء</h4>
            <p>أضف أسماء جميع المشاركين في ماراثون القراءة. يمكنك إضافة المزيد لاحقاً!</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("initial_members_form"):
            st.markdown("### ✏️ أدخل أسماء المشاركين")
            names_str = st.text_area(
                "اكتب كل اسم في سطر منفصل:", 
                height=150, 
                placeholder="مثال:\nخالد أحمد\nسارة محمد\nعلي حسن\nفاطمة عبدالله"
            )
            
            col1, col2 = st.columns([1, 2])
            with col2:
                if st.form_submit_button("✨ إضافة الأعضاء وحفظهم", use_container_width=True, type="primary"):
                    names = [name.strip() for name in names_str.split('\n') if name.strip()]
                    if names:
                        with st.spinner("🔮 جاري إضافة الأعضاء..."):
                            db.add_members(user_id, names)
                        st.success("🎉 تمت إضافة الأعضاء بنجاح! سيتم تحديث الصفحة للمتابعة إلى الخطوة التالية.")
                        st.balloons()
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error("⚠️ يرجى إدخال اسم واحد على الأقل.")

    # Step 2: Create Google Tools
    elif not user_settings.get("spreadsheet_url") or not user_settings.get("form_url"):
        st.markdown('<div class="step-indicator">الخطوة 2 من 3</div>', unsafe_allow_html=True)
        st.header("🛠️ إنشاء أدوات جوجل")
        
        st.markdown("""
        <div class="feature-card">
            <h4>📊 إنشاء الأدوات الذكية</h4>
            <p>سيقوم التطبيق بإنشاء جدول بيانات ونموذج تسجيل في حسابك تلقائياً!</p>
        </div>
        """, unsafe_allow_html=True)
        
        if 'sheet_title' not in st.session_state:
            st.session_state.sheet_title = f"بيانات ماراثون القراءة - {user_email.split('@')[0]}"
        
        st.markdown("### 🎨 اختر اسماً لأدواتك")
        st.session_state.sheet_title = st.text_input(
            "سيتم تطبيق هذا الاسم على جدول البيانات والنموذج:", 
            value=st.session_state.sheet_title
        )

        col1, col2 = st.columns([1, 2])
        with col2:
            if st.button("🌟 إنشاء الشيت والفورم الآن", type="primary", use_container_width=True):
                # Create Spreadsheet
                with st.spinner("📊 جاري إنشاء جدول البيانات..."):
                    try:
                        spreadsheet = gc.create(st.session_state.sheet_title)
                        db.set_user_setting(user_id, "spreadsheet_url", spreadsheet.url)
                        st.success("✅ تم إنشاء جدول البيانات بنجاح!")
                    except Exception as e:
                        st.error(f"❌ خطأ في إنشاء الشيت: {e}")
                        st.stop()

                # Create Form
                with st.spinner("📝 جاري إنشاء نموذج التسجيل..."):
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

                        member_question_id = update_result['replies'][1]['createItem']['itemId']
                        db.set_user_setting(user_id, "form_id", form_id)
                        db.set_user_setting(user_id, "member_question_id", member_question_id)
                        db.set_user_setting(user_id, "form_url", form_result['responderUri'])

                        st.success("✅ تم إنشاء النموذج وحفظ إعداداته بنجاح!")
                    except Exception as e:
                        st.error(f"❌ خطأ في إنشاء الفورم: {e}")
                        st.stop()

                # Final linking instructions
                st.markdown("---")
                st.markdown('<div class="step-indicator">خطوة الربط النهائية</div>', unsafe_allow_html=True)
                st.header("🔗 الربط والتحقق")
                
                st.markdown("""
                <div class="feature-card">
                    <h4>⚠️ خطوات مهمة جداً</h4>
                    <p>هذه الخطوات ضرورية ويجب القيام بها مرة واحدة فقط لضمان عمل التطبيق بشكل صحيح.</p>
                </div>
                """, unsafe_allow_html=True)
                
                editor_url = f"https://docs.google.com/forms/d/{form_id}/edit"

                st.markdown("### 📋 اتبع هذه الخطوات بعناية:")
                st.markdown("**1. 🔗 افتح النموذج للتعديل** من الرابط أدناه:")
                st.code(editor_url)
                st.markdown("**2. 📊 انتقل إلى تبويب 'الردود' (Responses)**")
                st.markdown("**3. 🔗 اضغط على أيقونة 'Link to Sheets'** (أيقونة جدول البيانات الخضراء)")
                st.markdown("**4. 📝 اختر 'Select existing spreadsheet'** واختر جدول البيانات بنفس الاسم")
                st.markdown("**5. ⚡ خطوة حاسمة:** أعد تسمية الورقة الجديدة إلى `Form Responses 1` بالضبط")
                st.markdown("**6. 🌍 للتواريخ:** File > Settings > غيّر Locale إلى United Kingdom > Save settings")

                col1, col2 = st.columns([1, 2])
                with col2:
                    if st.button("🔍 تحقق من الإعدادات وتابع", type="primary", use_container_width=True):
                        with st.spinner("🔍 جاري التحقق من الإعدادات..."):
                            try:
                                spreadsheet = gc.open_by_url(user_settings.get("spreadsheet_url"))
                                worksheet = spreadsheet.worksheet("Form Responses 1")
                                st.success("🎉 تم التحقق بنجاح! تم العثور على ورقة 'Form Responses 1'.")
                                try:
                                    default_sheet = spreadsheet.worksheet('Sheet1')
                                    spreadsheet.del_worksheet(default_sheet)
                                    st.info("🗑️ تم حذف ورقة 'Sheet1' الفارغة بنجاح.")
                                except gspread.exceptions.WorksheetNotFound:
                                    pass
                                time.sleep(2)
                                st.rerun()
                            except gspread.exceptions.WorksheetNotFound:
                                st.error("❌ فشل التحقق. لم نتمكن من العثور على ورقة باسم 'Form Responses 1'. يرجى التأكد من إعادة تسمية الورقة بالضبط.")
                            except Exception as e:
                                st.error(f"❌ حدث خطأ أثناء محاولة الوصول لجدول البيانات: {e}")

    # Step 3: Create First Challenge
    elif periods_df.empty:
        st.markdown('<div class="step-indicator">الخطوة 3 من 3</div>', unsafe_allow_html=True)
        st.header("🎯 إنشاء أول تحدي لك")
        
        st.markdown("""
        <div class="feature-card">
            <h4>🏁 خط النهاية!</h4>
            <p>أنت على وشك الانتهاء! كل ما عليك فعله هو إضافة تفاصيل أول كتاب وتحدي للبدء.</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("new_challenge_form", clear_on_submit=True):
            st.markdown("### 📖 تفاصيل الكتاب الأول")
            
            col1, col2 = st.columns(2)
            with col1:
                st.text_input("🏷️ عنوان الكتاب المشترك الأول", key="book_title")
                st.number_input("📅 سنة النشر", key="pub_year", value=date.today().year, step=1)
                st.date_input("📅 تاريخ نهاية التحدي", key="end_date", value=date.today() + timedelta(days=30))
            
            with col2:
                st.text_input("✍️ اسم المؤلف", key="book_author")
                st.date_input("🚀 تاريخ بداية التحدي", key="start_date", value=date.today())
            
            st.markdown("---")
            col1, col2 = st.columns([1, 2])
            with col2:
                if st.form_submit_button("🎉 بدء التحدي الأول!", use_container_width=True, type="primary"):
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
                            success, message = db.add_book_and_challenge(user_id, book_info, challenge_info, default_rules)
                            if success:
                                st.success("🎉 اكتمل الإعداد! تم إنشاء أول تحدي بنجاح.")
                                st.balloons()
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error(f"❌ فشلت العملية: {message}")
                        else:
                            st.error("❌ لم يتم العثور على الإعدادات الافتراضية في قاعدة البيانات.")
                    else:
                        st.error("⚠️ بيانات غير مكتملة: يرجى إدخال عنوان الكتاب واسم المؤلف.")

else:
    # --- ENHANCED MAIN WELCOME PAGE ---
    st.markdown('<div class="welcome-icon">🎉</div>', unsafe_allow_html=True)
    st.title("أهلاً بك في لوحة تحكم ماراثون القراءة")
    st.markdown("---")
    
    st.markdown("""
    <div class="feature-card">
        <h3>✨ اكتمل إعداد حسابك بنجاح!</h3>
        <p>يمكنك الآن الاستفادة من جميع مميزات التطبيق والتنقل بين الصفحات المختلفة.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🚀 ماذا يمكنك أن تفعل الآن؟")
    
    # Feature cards
    features = [
        {
            "icon": "📈",
            "title": "لوحة التحكم العامة",
            "description": "احصل على نظرة شاملة على أداء جميع المشاركين في كل التحديات"
        },
        {
            "icon": "🎯", 
            "title": "تحليلات التحديات",
            "description": "اغوص في تفاصيل تحدي معين وقارن أداء المشاركين فيه"
        },
        {
            "icon": "⚙️",
            "title": "الإدارة والإعدادات", 
            "description": "أضف أعضاء جدد، أنشئ تحديات مستقبلية، أو عدّل نظام النقاط"
        },
        {
            "icon": "❓",
            "title": "عن التطبيق",
            "description": "اعرف المزيد عن المشروع وكيفية عمل نظام النقاط"
        }
    ]
    
    for feature in features:
        st.markdown(f"""
        <div class="feature-card">
            <h4>{feature['icon']} {feature['title']}</h4>
            <p>{feature['description']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("""
    <div class="feature-card">
        <h4>🌟 نصيحة للبدء</h4>
        <p>ابدأ بالذهاب إلى <strong>'Overall Dashboard'</strong> من الشريط الجانبي لرؤية الصورة الكاملة لماراثون القراءة!</p>
    </div>
    """, unsafe_allow_html=True)