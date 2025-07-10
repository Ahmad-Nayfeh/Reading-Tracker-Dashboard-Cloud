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

def authenticate():
    """
    Handles the complete Google OAuth 2.0 flow with robust session persistence
    and error handling for missing refresh tokens. This is the final version.
    """
    CREDENTIALS_KEY = 'credentials_json'

    if "google_oauth_credentials" not in st.secrets:
        st.error("Secrets block [google_oauth_credentials] not found!")
        st.stop()

    client_config_dict = dict(st.secrets["google_oauth_credentials"])
    cloud_redirect_uri = "https://reading-marathon.streamlit.app"

    flow = Flow.from_client_config(
        client_config={'web': client_config_dict},
        scopes=SCOPES,
        redirect_uri=cloud_redirect_uri
    )

    authorization_code = st.query_params.get("code")

    # Block A: Handle the authorization code from Google
    if authorization_code:
        st.warning("--- DEBUG (auth_manager.py): Block A - Authorization code found in URL. Fetching token...")
        try:
            flow.fetch_token(code=authorization_code)
            creds_json = flow.credentials.to_json()
            st.session_state[CREDENTIALS_KEY] = creds_json
            
            # --- DIAGNOSTIC ---
            creds_info_for_debug = json.loads(creds_json)
            if 'refresh_token' in creds_info_for_debug:
                st.warning("--- DEBUG (auth_manager.py): SUCCESS! Refresh token received and stored.")
            else:
                st.warning("--- DEBUG (auth_manager.py): CRITICAL! Refresh token NOT received from Google.")
            # --- END DIAGNOSTIC ---

            st.query_params.clear()
            st.rerun()
        except Exception as e:
            st.error(f"فشل في الحصول على التوكن: {e}")
            st.stop()

    # Block B: Handle existing credentials in session state
    elif CREDENTIALS_KEY in st.session_state:
        st.warning("--- DEBUG (auth_manager.py): Block B - Found credentials in session_state. Processing...")
        creds_info = json.loads(st.session_state[CREDENTIALS_KEY])

        # --- ROBUST CREDENTIALS HANDLING ---
        if 'refresh_token' not in creds_info:
            st.warning("--- DEBUG (auth_manager.py): CRITICAL! No refresh_token in stored credentials. Forcing re-authentication.")
            del st.session_state[CREDENTIALS_KEY]
            st.rerun()

        creds = Credentials.from_authorized_user_info(creds_info, SCOPES)

        if creds.expired and creds.refresh_token:
            st.warning("--- DEBUG (auth_manager.py): Credentials expired. Attempting to refresh...")
            try:
                creds.refresh(Request())
                st.session_state[CREDENTIALS_KEY] = creds.to_json()
                st.warning("--- DEBUG (auth_manager.py): Refresh successful.")
            except Exception as e:
                st.error("انتهت صلاحية جلستك، يرجى تسجيل الدخول مرة أخرى.")
                st.warning(f"--- DEBUG (auth_manager.py): Refresh failed: {e}")
                del st.session_state[CREDENTIALS_KEY]
                st.rerun()
        
        if creds.valid:
            st.warning("--- DEBUG (auth_manager.py): Credentials are valid. Proceeding with app.")
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
            st.warning("--- DEBUG (auth_manager.py): Credentials are NOT valid. Forcing re-authentication.")
            del st.session_state[CREDENTIALS_KEY]
            st.rerun()

    # Block C: Show login button if no code and no credentials
    else:
        st.warning("--- DEBUG (auth_manager.py): Block C - No code and no credentials. Displaying login button.")
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
