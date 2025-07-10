import streamlit as st
import gspread
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
import db_manager as db
from googleapiclient.discovery import build
import os
import json

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
    Determines the correct redirect URI based on the execution environment.
    """
    st.warning("--- DEBUG: Executing get_redirect_uri() ---")
    
    # Check for the environment variable set by Streamlit Cloud.
    server_address = os.environ.get("STREAMLIT_SERVER_ADDRESS")
    st.warning(f"DEBUG: Value of os.environ.get('STREAMLIT_SERVER_ADDRESS') is: {server_address}")
    
    is_cloud = bool(server_address)
    st.warning(f"DEBUG: Is Cloud Environment? -> {is_cloud}")

    if is_cloud:
        uri = "https://reading-marathon.streamlit.app"
        st.warning(f"DEBUG: Cloud environment detected. Selected URI: {uri}")
        return uri
    else:
        uri = "http://localhost:8501"
        st.warning(f"DEBUG: Local environment detected. Selected URI: {uri}")
        return uri

def authenticate():
    """
    Handles the complete Google OAuth 2.0 flow with debugging messages.
    """
    st.warning("--- DEBUG: Starting authenticate() function ---")

    # Ensure Google OAuth credentials are present in secrets.
    if "google_oauth_credentials" not in st.secrets:
        st.error("🔑 **خطأ في الإعدادات:** لم يتم العثور على `google_oauth_credentials` في ملف الأسرار.")
        st.stop()

    creds_dict = dict(st.secrets["google_oauth_credentials"])
    redirect_uri = get_redirect_uri()

    # Create the OAuth Flow instance.
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
        
        st.warning("--- DEBUG: About to display the login button. ---")
        st.warning(f"DEBUG: The generated authorization URL contains this redirect_uri: {flow.redirect_uri}")
        # The line below is for you to see the full URL being generated.
        st.code(auth_url)

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