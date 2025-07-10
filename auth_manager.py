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
    Handles the complete Google OAuth 2.0 flow with extensive session state debugging.
    """
    st.warning("--- DEBUG: (1) Starting authenticate() function ---")

    if "google_oauth_credentials" not in st.secrets:
        st.error("Secrets block [google_oauth_credentials] not found!")
        st.stop()

    client_config_dict = dict(st.secrets["google_oauth_credentials"])
    st.warning("DEBUG: (2) Loaded [google_oauth_credentials] from secrets.")
    
    # HARDCODED REDIRECT URI FOR THE CLOUD ENVIRONMENT
    cloud_redirect_uri = "https://reading-marathon.streamlit.app"
    st.warning(f"DEBUG: (3) Forcing redirect_uri to be: {cloud_redirect_uri}")

    # Create the Flow instance
    flow = Flow.from_client_config(
        client_config={'web': client_config_dict},
        scopes=SCOPES,
        redirect_uri=cloud_redirect_uri
    )
    st.warning("DEBUG: (4) Flow object created successfully.")

    # Check for the authorization code in the URL
    authorization_code = st.query_params.get("code")
    st.warning(f"DEBUG: (5) Checking for authorization_code in URL. Found: {authorization_code}")

    # --- Authentication Flow Logic ---

    # Block A: Handle the authorization code from Google
    if authorization_code:
        st.warning("DEBUG: (A.1) `authorization_code` FOUND. Entering Block A.")
        try:
            st.warning("DEBUG: (A.2) Attempting to fetch token...")
            flow.fetch_token(code=authorization_code)
            st.warning("DEBUG: (A.3) Token fetched successfully.")
            st.session_state.credentials_json = flow.credentials.to_json()
            st.warning("DEBUG: (A.4) Credentials saved to session_state.")
            st.query_params.clear()
            st.warning("DEBUG: (A.5) Query params cleared. About to st.rerun().")
            st.rerun()
        except Exception as e:
            st.error(f"فشل في الحصول على التوكن: {e}")
            st.warning(f"DEBUG: (A.6) Exception during token fetch: {e}")
            st.stop()

    # Block B: Handle existing credentials in session state
    elif 'credentials_json' in st.session_state:
        st.warning("DEBUG: (B.1) `credentials_json` FOUND in session_state. Entering Block B.")
        creds_info = json.loads(st.session_state.credentials_json)
        # NEW DIAGNOSTIC: Let's see what keys Google returned (is 'refresh_token' one of them?)
        st.warning(f"DEBUG: (B.1.1) Keys in loaded credentials_json: {list(creds_info.keys())}")

        creds = Credentials.from_authorized_user_info(creds_info, SCOPES)
        st.warning(f"DEBUG: (B.2) Credentials loaded. Expired? -> {creds.expired}")
        # NEW DIAGNOSTIC: This is the most important check.
        st.warning(f"DEBUG: (B.2.1) Refresh token exists in creds object? -> {bool(creds.refresh_token)}")

        if creds.expired and creds.refresh_token:
            st.warning("DEBUG: (B.3) Credentials expired. Attempting to refresh...")
            try:
                creds.refresh(Request())
                st.session_state.credentials_json = creds.to_json()
                st.warning("DEBUG: (B.4) Credentials refreshed successfully.")
            except Exception as e:
                st.error("انتهت صلاحية جلستك، يرجى تسجيل الدخول مرة أخرى.")
                st.warning(f"DEBUG: (B.5) Exception during refresh: {e}. Deleting creds and rerunning.")
                del st.session_state.credentials_json
                st.rerun()
        
        st.warning(f"DEBUG: (B.6) Checking if credentials are valid. Valid? -> {creds.valid}")
        if creds.valid:
            st.warning("DEBUG: (B.7) Credentials are valid. Checking for user_id in session_state.")
            if 'user_id' not in st.session_state:
                st.warning("DEBUG: (B.8) `user_id` NOT FOUND. Fetching user info from Google.")
                userinfo_service = build('oauth2', 'v2', credentials=creds)
                user_info = userinfo_service.userinfo().get().execute()
                st.session_state.user_id = user_info.get('id')
                st.session_state.user_email = user_info.get('email')
                st.warning(f"DEBUG: (B.9) User info fetched: {st.session_state.user_email}")
                
                if not db.check_user_exists(st.session_state.user_id):
                    st.warning("DEBUG: (B.10) New user detected. Creating workspace...")
                    with st.spinner("أهلاً بك! جاري تجهيز مساحة العمل الخاصة بك لأول مرة..."):
                        db.create_new_user_workspace(st.session_state.user_id, st.session_state.user_email)
            
            st.warning("DEBUG: (B.11) Authentication successful. Returning credentials.")
            return creds

    # Block C: Show login button if no code and no credentials
    else:
        st.warning("DEBUG: (C.1) No code and no credentials. Entering Block C to show login button.")
        # 'access_type='offline'' is crucial to get a refresh token.
        # 'prompt='consent'' forces the consent screen to appear, which helps in debugging to ensure a refresh token is issued.
        auth_url, _ = flow.authorization_url(access_type='offline', prompt='consent')
        st.warning(f"DEBUG: (C.2) Generated auth_url. It contains redirect_uri: {cloud_redirect_uri}")
        st.title("🚀 أهلاً بك في \"ماراثون القراءة\"")
        st.info("للبدء، يرجى ربط حسابك في جوجل.")
        st.link_button("🔗 **الربط بحساب جوجل والبدء**", auth_url, use_container_width=True, type="primary")
        st.warning("DEBUG: (C.3) Login button displayed. About to st.stop().")
        st.stop()


@st.cache_resource
def get_gspread_client(user_id: str, _creds: Credentials):
    if not _creds or not _creds.valid:
        st.error("🔒 **خطأ في المصادقة:** لم يتم تمرير بيانات اعتماد صالحة.")
        st.stop()
    return gspread.authorize(_creds)
