import streamlit as st
import gspread
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
import db_manager as db
from googleapiclient.discovery import build
import os
import json
import socket

# The scopes required by the application.
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/forms.body",
    "openid",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email"
]

def get_correct_uri():
    """
    Determines the single correct redirect URI based on the execution environment's hostname.
    """
    st.warning("--- DEBUG: Executing get_correct_uri() ---")
    try:
        hostname = socket.gethostname()
        st.warning(f"DEBUG: Detected hostname: {hostname}")
        if 'streamlit' in hostname:
            st.warning("DEBUG: 'streamlit' in hostname. Selecting CLOUD URI.")
            return "https://reading-marathon.streamlit.app"
        else:
            st.warning("DEBUG: 'streamlit' not in hostname. Selecting LOCAL URI.")
            return "http://localhost:8501"
    except Exception as e:
        st.error(f"Error detecting hostname: {e}")
        return "http://localhost:8501"

def authenticate():
    """
    Handles the complete Google OAuth 2.0 flow by loading a unified configuration
    and explicitly setting the redirect URI.
    """
    st.warning("--- DEBUG: Starting authenticate() function ---")

    if "google_oauth_credentials" not in st.secrets:
        st.error("Secrets block [google_oauth_credentials] not found!")
        st.stop()

    # Load the unified credentials block.
    client_config_dict = dict(st.secrets["google_oauth_credentials"])
    st.warning("DEBUG: Loaded [google_oauth_credentials] from secrets.")
    
    # Determine the correct URI to pass to the Flow object.
    correct_redirect_uri = get_correct_uri()
    st.warning(f"DEBUG: Determined correct redirect_uri to be passed to Flow: {correct_redirect_uri}")

    # Create the Flow instance, explicitly passing the redirect_uri.
    # Since the config from secrets no longer contains 'redirect_uris',
    # the library is forced to use the one we provide here.
    flow = Flow.from_client_config(
        client_config={'web': client_config_dict},
        scopes=SCOPES,
        redirect_uri=correct_redirect_uri
    )
    st.warning("DEBUG: Flow object created successfully.")

    # --- The rest of the authentication logic remains the same ---
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
        st.info("للبدء، يرجى ربط حسابك في جوجل.")
        st.link_button("🔗 **الربط بحساب جوجل والبدء**", auth_url, use_container_width=True, type="primary")
        st.stop()


@st.cache_resource
def get_gspread_client(user_id: str, _creds: Credentials):
    if not _creds or not _creds.valid:
        st.error("🔒 **خطأ في المصادقة:** لم يتم تمرير بيانات اعتماد صالحة.")
        st.stop()
    return gspread.authorize(_creds)