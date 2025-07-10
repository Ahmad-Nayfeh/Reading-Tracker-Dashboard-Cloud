import streamlit as st
import gspread
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
import db_manager as db
from googleapiclient.discovery import build
import json

# --- Configuration ---
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/forms.body",
    "openid",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email"
]
SESSION_STATE_KEY = 'google_credentials'

def _get_flow():
    """Creates and returns a Google OAuth Flow object."""
    client_config_dict = dict(st.secrets["google_oauth_credentials"])
    return Flow.from_client_config(
        client_config={'web': client_config_dict},
        scopes=SCOPES,
        redirect_uri="https://reading-marathon.streamlit.app"
    )

def _rebuild_credentials_from_db(user_id):
    """
    Attempts to rebuild a valid credential object using the refresh token
    stored in Firestore. This is the core of the F5-proof logic.
    """
    st.warning("--- DEBUG: Attempting to restore session from DB... ---")
    refresh_token = db.get_refresh_token(user_id)

    if not refresh_token:
        st.warning("--- DEBUG: No refresh token found in DB for this user. ---")
        return None

    st.warning("--- DEBUG: Refresh token found in DB. Attempting to refresh... ---")
    client_config = dict(st.secrets["google_oauth_credentials"])
    try:
        creds = Credentials(
            token=None,  # No access token yet
            refresh_token=refresh_token,
            token_uri='https://oauth2.googleapis.com/token',
            client_id=client_config.get("client_id"),
            client_secret=client_config.get("client_secret"),
            scopes=SCOPES
        )
        creds.refresh(Request())
        st.warning("--- DEBUG: DB session restore successful! ---")
        return creds
    except Exception as e:
        st.warning(f"--- DEBUG: Failed to refresh token from DB: {e} ---")
        # This could mean the user revoked access. The token is now invalid.
        return None

def authenticate():
    """
    Handles the complete Google OAuth 2.0 flow with Firestore-backed persistence.
    """
    st.warning("--- DEBUG: `authenticate()` called. ---")

    # Priority 1: Check for a valid session in st.session_state (for multi-page navigation)
    if SESSION_STATE_KEY in st.session_state:
        creds = Credentials.from_authorized_user_info(json.loads(st.session_state[SESSION_STATE_KEY]))
        if creds.valid:
            st.warning("--- DEBUG: Found valid credentials in st.session_state. ---")
            return creds
        elif creds.expired and creds.refresh_token:
            st.warning("--- DEBUG: Credentials in session expired. Refreshing... ---")
            creds.refresh(Request())
            st.session_state[SESSION_STATE_KEY] = creds.to_json()
            return creds

    # Priority 2: Handle the redirect from Google's login screen
    authorization_code = st.query_params.get("code")
    if authorization_code:
        st.warning("--- DEBUG: Auth code found in URL. ---")
        flow = _get_flow()
        flow.fetch_token(code=authorization_code)
        creds = flow.credentials

        if not creds.refresh_token:
            st.error("### 🔴 فشل المصادقة: لم يتم استلام مفتاح الجلسة الدائمة (Refresh Token)")
            st.info("لإصلاح ذلك، يرجى إلغاء وصول التطبيق من إعدادات حسابك في جوجل ثم المحاولة مرة أخرى.")
            st.markdown("[رابط صفحة أذونات حساب جوجل](https://myaccount.google.com/permissions)")
            st.stop()
        
        st.warning("--- DEBUG: Refresh token received successfully! ---")
        userinfo_service = build('oauth2', 'v2', credentials=creds)
        user_info = userinfo_service.userinfo().get().execute()
        user_id = user_info.get('id')
        user_email = user_info.get('email')

        if not db.check_user_exists(user_id):
            db.create_new_user_workspace(user_id, user_email)
        
        st.warning("--- DEBUG: Saving refresh token to Firestore... ---")
        db.save_refresh_token(user_id, creds.refresh_token)

        st.session_state.user_id = user_id
        st.session_state.user_email = user_email
        st.session_state[SESSION_STATE_KEY] = creds.to_json()
        
        st.query_params.clear()
        st.query_params['user_id'] = user_id # Add user_id to URL for F5 recovery
        st.rerun()

    # Priority 3: Handle F5 refresh by checking for user_id in URL
    user_id_from_params = st.query_params.get("user_id")
    if user_id_from_params:
        st.warning(f"--- DEBUG: Found user_id '{user_id_from_params}' in URL. Attempting DB restore. ---")
        creds = _rebuild_credentials_from_db(user_id_from_params)
        if creds and creds.valid:
            userinfo_service = build('oauth2', 'v2', credentials=creds)
            user_info = userinfo_service.userinfo().get().execute()
            st.session_state.user_id = user_info.get('id')
            st.session_state.user_email = user_info.get('email')
            st.session_state[SESSION_STATE_KEY] = creds.to_json()
            st.rerun()

    # Priority 4: If all else fails, show the login button
    st.warning("--- DEBUG: No valid session found. Displaying login button. ---")
    flow = _get_flow()
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
