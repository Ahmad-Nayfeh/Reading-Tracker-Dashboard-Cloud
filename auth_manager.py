import streamlit as st
import gspread
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
import os
import db_manager as db # <-- استيراد مدير قاعدة البيانات الجديد
from googleapiclient.discovery import build

# --- Configuration Constants ---
CLIENT_SECRET_FILE = 'client_secret.json'
TOKEN_FILE_DIR = 'data' # سيتم إنشاء المجلد إذا لم يكن موجوداً
# اسم ملف التوكن الآن سيعتمد على هوية المستخدم ليدعم تسجيلات دخول متعددة على نفس الجهاز
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/forms.body",
    "openid", # <-- صلاحية جديدة للحصول على معلومات المستخدم الأساسية
    "https://www.googleapis.com/auth/userinfo.profile", # <-- صلاحية جديدة للحصول على معلومات البروفايل
    "https://www.googleapis.com/auth/userinfo.email" # <-- صلاحية جديدة للحصول على الإيميل
]

def get_token_path(user_id):
    """
    ينشئ مسارًا فريدًا لملف التوكن الخاص بكل مستخدم.
    """
    return os.path.join(TOKEN_FILE_DIR, f'token_{user_id}.json')

def authenticate():
    """
    The main authentication function. It handles all authentication logic
    in a robust, sequential way that is compatible with Streamlit and Firestore.

    Returns:
        google.oauth2.credentials.Credentials: A valid user credential object.
    """
    # التحقق من وجود بيانات المستخدم في الـ session state أولاً
    if 'user_id' in st.session_state and 'credentials' in st.session_state:
        return st.session_state.credentials

    # إذا لم تكن موجودة، نبدأ عملية المصادقة
    try:
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRET_FILE,
            scopes=SCOPES,
            redirect_uri='http://localhost:8501'
        )
    except FileNotFoundError:
        st.error(f"🔑 **خطأ في الإعدادات:** لم يتم العثور على ملف `{CLIENT_SECRET_FILE}`. يرجى التأكد من اتباع إرشادات الإعداد ووضع الملف في المجلد الرئيسي للمشروع.")
        st.stop()

    authorization_code = st.query_params.get("code")
    
    if authorization_code:
        # إذا كنا في مرحلة العودة من جوجل مع كود المصادقة
        flow.fetch_token(code=authorization_code)
        creds = flow.credentials
        
        # --- الإضافة الجديدة هنا: التحقق من المستخدم وإنشاء مساحة عمل ---
        try:
            # استخدام الصلاحيات للحصول على معلومات المستخدم
            userinfo_service = build('oauth2', 'v2', credentials=creds)
            user_info = userinfo_service.userinfo().get().execute()
            
            user_id = user_info.get('id')
            user_email = user_info.get('email')

            if not user_id or not user_email:
                st.error("لم نتمكن من الحصول على معرّف المستخدم من جوجل. يرجى المحاولة مرة أخرى.")
                st.stop()

            # تخزين معلومات المستخدم في الـ session state
            st.session_state.user_id = user_id
            st.session_state.user_email = user_email
            st.session_state.credentials = creds

            # التحقق مما إذا كان المستخدم جديدًا
            if not db.check_user_exists(user_id):
                # إذا كان جديدًا، قم بإنشاء مساحة عمل له
                with st.spinner("أهلاً بك! جاري تجهيز مساحة العمل الخاصة بك لأول مرة..."):
                    db.create_new_user_workspace(user_id, user_email)
            
            # حفظ صلاحيات الدخول في ملف خاص بهذا المستخدم
            save_credentials_to_file(creds, user_id)

        except Exception as e:
            st.error(f"حدث خطأ أثناء الحصول على معلومات المستخدم أو إنشاء مساحة العمل: {e}")
            st.stop()
        
        # مسح الـ query parameters من الرابط وإعادة تشغيل التطبيق
        st.query_params.clear()
        st.rerun()
    
    else:
        # إذا لم نكن في مرحلة العودة، نعرض زر تسجيل الدخول
        auth_url, _ = flow.authorization_url(prompt='consent')
        st.title("🚀 أهلاً بك في \"ماراثون القراءة\"")
        st.info("للبدء، يرجى ربط حسابك في جوجل. سيقوم التطبيق بإنشاء مساحة عمل سحابية خاصة بك لإدارة تحديات القراءة بكل سهولة.")
        st.link_button("🔗 **الربط بحساب جوجل والبدء**", auth_url, use_container_width=True, type="primary")
        st.stop()


def save_credentials_to_file(creds, user_id):
    """
    يحفظ صلاحيات المستخدم في ملف JSON خاص به.
    """
    os.makedirs(TOKEN_FILE_DIR, exist_ok=True)
    token_path = get_token_path(user_id)
    with open(token_path, 'w') as token:
        token.write(creds.to_json())


@st.cache_resource
def get_gspread_client():
    """
    يستخدم صلاحيات الدخول المخزنة لإنشاء gspread client.
    """
    creds = st.session_state.get('credentials')
    if not creds:
        st.error("🔒 **خطأ في المصادقة:** لم نتمكن من التحقق من صلاحيات الوصول.")
        st.stop()
    return gspread.authorize(creds)
