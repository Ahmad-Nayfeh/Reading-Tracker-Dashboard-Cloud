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
        try:
            flow.fetch_token(code=authorization_code)
            st.session_state[CREDENTIALS_KEY] = flow.credentials.to_json()
            st.query_params.clear()
            st.rerun()
        except Exception as e:
            st.error(f"فشل في الحصول على التوكن: {e}")
            st.stop()

    # Block B: Handle existing credentials in session state
    elif CREDENTIALS_KEY in st.session_state:
        creds_info = json.loads(st.session_state[CREDENTIALS_KEY])

        # --- ROBUST CREDENTIALS HANDLING ---
        # This is the critical fix. We check for the refresh token BEFORE
        # trying to create the Credentials object, preventing the crash.
        if 'refresh_token' not in creds_info:
            # If the refresh token is missing, the stored credentials are not useful
            # for persistent sessions. We must clear them and force re-authentication.
            st.warning("جلسة غير مكتملة، يرجى إعادة تسجيل الدخول للحصول على جلسة دائمة.")
            del st.session_state[CREDENTIALS_KEY]
            st.rerun()

        creds = Credentials.from_authorized_user_info(creds_info, SCOPES)

        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                st.session_state[CREDENTIALS_KEY] = creds.to_json()
            except Exception as e:
                st.error("انتهت صلاحية جلستك، يرجى تسجيل الدخول مرة أخرى.")
                del st.session_state[CREDENTIALS_KEY]
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
            # This case should be rare now, but it's good practice to handle it.
            st.error("بيانات الاعتماد غير صالحة. يرجى تسجيل الدخول مرة أخرى.")
            del st.session_state[CREDENTIALS_KEY]
            st.rerun()

    # Block C: Show login button if no code and no credentials
    else:
        # We use both 'access_type' and 'prompt' to maximize the chance
        # of getting a refresh token on the first login after revoking access.
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
