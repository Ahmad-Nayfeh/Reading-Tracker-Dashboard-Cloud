import streamlit as st
import gspread
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
import db_manager as db
from googleapiclient.discovery import build
import os
import json
import socket # استيراد المكتبة الجديدة

# The scopes required by the application.
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/forms.body",
    "openid",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email"
]

def get_redirect_uri():
    """
    Determines the correct redirect URI using a more robust method.
    """
    try:
        # Get the hostname of the machine the script is running on.
        hostname = socket.gethostname()
        # On Streamlit Cloud, the hostname will contain 'streamlit'.
        if 'streamlit' in hostname:
            return "https://reading-marathon.streamlit.app"
        else:
            # Otherwise, we assume it's a local environment.
            return "http://localhost:8501"
    except Exception:
        # Fallback for any unforeseen errors.
        return "http://localhost:8501"


def authenticate():
    """
    Handles the complete Google OAuth 2.0 flow using the corrected logic.
    """
    if "google_oauth_credentials" not in st.secrets:
        st.error("🔑 **خطأ في الإعدادات:** لم يتم العثور على `google_oauth_credentials` في ملف الأسرار.")
        st.stop()

    creds_dict = dict(st.secrets["google_oauth_credentials"])
    redirect_uri = get_redirect_uri()

    flow = Flow.from_client_config(
        client_config={'web': creds_dict},
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )

    authorization_code = st.query_params.get("code")

    if authorization_code:
        try:
            flow.fetch_token(code=authorization_code)
            st.session_state.credentials_json = flow.credentials.to_json()
            st.query_params.clear()
            st.rerun()
        except Exception as e:
            st.error(f"فشل في الحصول على التوكن: {e}")
            st.stop()

    elif 'credentials_json' in st.session_state:
        creds_info = json.loads(st.session_state.credentials_json)
        creds = Credentials.from_authorized_user_info(creds_info, SCOPES)

        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                st.session_state.credentials_json = creds.to_json()
            except Exception as e:
                st.error("انتهت صلاحية جلستك، يرجى تسجيل الدخول مرة أخرى.")
                del st.session_state.credentials_json
                st.rerun()
        
        if creds.valid:
            if 'user_id' not in st.session_state:
                userinfo_service = build('oauth2', 'v2', credentials=creds)
                user_info = userinfo_service.userinfo().get().execute()
                st.session_state.user_id = user_info.get('id')
                st.session_state.user_email = user_info.get('email')
                
                if not db.check_user_exists(st.session_state.user_id):
                    with st.spinner("أهلاً بك! جاري تجهيز مساحة العمل الخاصة بك لأول مرة..."):
                        db.create_new_user_workspace(st.session_state.user_id, st.session_state.user_email)
            
            return creds

    else:
        auth_url, _ = flow.authorization_url(access_type='offline', prompt='consent')
        
        st.title("🚀 أهلاً بك في \"ماراثون القراءة\"")
        st.info("للبدء، يرجى ربط حسابك في جوجل. سيقوم التطبيق بإنشاء مساحة عمل سحابية خاصة بك لإدارة تحديات القراءة بكل سهولة.")
        st.link_button("🔗 **الربط بحساب جوجل والبدء**", auth_url, use_container_width=True, type="primary")
        st.stop()

@st.cache_resource
def get_gspread_client(user_id: str, _creds: Credentials):
    if not _creds or not _creds.valid:
        st.error("🔒 **خطأ في المصادقة:** لم يتم تمرير بيانات اعتماد صالحة.")
        st.stop()
    return gspread.authorize(_creds)