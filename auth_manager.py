import streamlit as st
import gspread
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
import os
import db_manager as db 
from googleapiclient.discovery import build
import json

# --- Configuration Constants ---
CLIENT_SECRET_FILE = 'client_secret.json'
# --- تعديل رئيسي: سنستخدم ملف توكن واحد وثابت ---
# هذا يبسط عملية المصادقة للجلسات المستمرة في بيئة النشر
TOKEN_DIR = 'data'
TOKEN_FILE = os.path.join(TOKEN_DIR, 'token.json') 

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/forms.body",
    "openid",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email"
]

def save_credentials(creds):
    """
    دالة جديدة ومبسطة لحفظ صلاحيات الدخول في ملف التوكن الثابت.
    """
    os.makedirs(TOKEN_DIR, exist_ok=True)
    with open(TOKEN_FILE, 'w') as token:
        token.write(creds.to_json())

def load_credentials():
    """
    دالة جديدة لتحميل صلاحيات الدخول من ملف التوكن إن وجد.
    """
    if os.path.exists(TOKEN_FILE):
        return Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    return None

def authenticate():
    """
    ## دالة المصادقة الرئيسية (مُعاد بناؤها بالكامل) ##
    تتعامل مع منطق المصادقة بشكل ذكي ومستمر.
    
    التسلسل المنطقي الجديد:
    1.  التحقق من وجود صلاحيات صالحة في الجلسة الحالية (st.session_state).
    2.  إذا لم توجد، محاولة تحميل الصلاحيات من ملف التوكن المحفوظ (token.json).
    3.  تحديث الصلاحيات تلقائياً إذا كانت منتهية الصلاحية (باستخدام الـ refresh token).
    4.  إذا لم ينجح أي مما سبق، تبدأ عملية المصادقة الكاملة للمستخدم الجديد.
    """
    # الخطوة 1: التحقق من الجلسة الحالية لتسريع التنقل داخل التطبيق
    if 'credentials' in st.session_state and st.session_state.credentials.valid:
        return st.session_state.credentials

    # الخطوة 2: محاولة تحميل الصلاحيات من الملف المحفوظ (للمستخدم العائد)
    creds = load_credentials()
    
    if creds:
        # التحقق مما إذا كانت الصلاحيات منتهية، وتحديثها بصمت إن أمكن
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                save_credentials(creds) # حفظ الصلاحيات المحدثة
            except Exception as e:
                st.error("انتهت صلاحية جلسة الدخول. يرجى تسجيل الدخول مرة أخرى.")
                # في حال فشل التحديث، قم بإزالة الملف الفاسد لتبدأ عملية مصادقة جديدة
                if os.path.exists(TOKEN_FILE):
                    os.remove(TOKEN_FILE)
                creds = None # إعادة التعيين إلى None للمتابعة لصفحة تسجيل الدخول

        # إذا كانت الصلاحيات صالحة (أو تم تحديثها بنجاح)، قم بتعبئة الـ session_state
        if creds and creds.valid:
            try:
                userinfo_service = build('oauth2', 'v2', credentials=creds)
                user_info = userinfo_service.userinfo().get().execute()
                user_id = user_info.get('id')

                # إذا لم نتمكن من الحصول على user_id، فهذا يعني أن الصلاحيات قد تكون غير كافية
                if not user_id:
                     raise Exception("لم يتم العثور على معرّف المستخدم في الصلاحيات.")

                st.session_state.user_id = user_id
                st.session_state.user_email = user_info.get('email')
                st.session_state.credentials = creds
                return creds
            except Exception as e:
                # إذا حدث خطأ أثناء جلب معلومات المستخدم، ربما الصلاحيات غير سليمة
                st.warning(f"حدث خطأ أثناء التحقق من الصلاحيات: {e}. قد تحتاج لتسجيل الدخول مجدداً.")
                if os.path.exists(TOKEN_FILE):
                    os.remove(TOKEN_FILE)
    
    # --- بداية منطق المصادقة للمستخدم الجديد (إذا فشلت كل المحاولات السابقة) ---

    # إعداد flow المصادقة
    if 'google_oauth_credentials' in st.secrets:
        creds_dict = st.secrets["google_oauth_credentials"]
        flow = Flow.from_client_config(
            client_config={'web': creds_dict},
            scopes=SCOPES,
            redirect_uri='https://reading-marathon.streamlit.app'
        )
    else:
        try:
            flow = Flow.from_client_secrets_file(
                CLIENT_SECRET_FILE,
                scopes=SCOPES,
                redirect_uri='http://localhost:8501'
            )
        except FileNotFoundError:
            st.error(f"🔑 **خطأ في الإعدادات:** لم يتم العثور على ملف `{CLIENT_SECRET_FILE}`.")
            st.stop()

    # التحقق من وجود كود المصادقة في رابط URL
    authorization_code = st.query_params.get("code")
    
    if authorization_code:
        # إذا كنا في مرحلة العودة من جوجل مع كود المصادقة
        flow.fetch_token(code=authorization_code)
        creds = flow.credentials
        
        # حفظ الصلاحيات الجديدة في الملف للمستقبل
        save_credentials(creds)
        
        # الحصول على معلومات المستخدم والتحقق من مساحة العمل
        try:
            userinfo_service = build('oauth2', 'v2', credentials=creds)
            user_info = userinfo_service.userinfo().get().execute()
            
            user_id = user_info.get('id')
            user_email = user_info.get('email')

            if not user_id or not user_email:
                st.error("لم نتمكن من الحصول على معرّف المستخدم من جوجل. يرجى المحاولة مرة أخرى.")
                st.stop()

            st.session_state.user_id = user_id
            st.session_state.user_email = user_email
            st.session_state.credentials = creds

            if not db.check_user_exists(user_id):
                with st.spinner("أهلاً بك! جاري تجهيز مساحة العمل الخاصة بك لأول مرة..."):
                    db.create_new_user_workspace(user_id, user_email)
            
        except Exception as e:
            st.error(f"حدث خطأ أثناء الحصول على معلومات المستخدم أو إنشاء مساحة العمل: {e}")
            st.stop()
        
        # مسح الـ query parameters من الرابط وإعادة تشغيل التطبيق
        st.query_params.clear()
        st.rerun()
    
    else:
        # إذا لم يكن هناك أي صلاحيات محفوظة أو كود مصادقة، نعرض زر تسجيل الدخول
        auth_url, _ = flow.authorization_url(prompt='consent')
        st.title("🚀 أهلاً بك في \"ماراثون القراءة\"")
        st.info("للبدء، يرجى ربط حسابك في جوجل. سيقوم التطبيق بإنشاء مساحة عمل سحابية خاصة بك لإدارة تحديات القراءة بكل سهولة.")
        st.link_button("🔗 **الربط بحساب جوجل والبدء**", auth_url, use_container_width=True, type="primary")
        st.stop()

@st.cache_resource
def get_gspread_client(_creds: Credentials):
    """
    لم يتم تغيير هذه الدالة، ولكن تم تعديل الوسيط _creds ليكون بدون تحديد نوع
    لأن st.cache_resource لا تتعامل جيداً مع أنواع الكائنات المعقدة.
    """
    if not _creds or not _creds.valid:
        st.error("🔒 **خطأ في المصادقة:** لم يتم تمرير بيانات اعتماد صالحة.")
        st.stop()
    return gspread.authorize(_creds)