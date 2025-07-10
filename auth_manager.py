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

CREDENTIALS_KEY = 'credentials_json'

def authenticate():
    """
    Handles the complete Google OAuth 2.0 flow with robust session persistence
    by ensuring a refresh_token is always present.
    """
    if "google_oauth_credentials" not in st.secrets:
        st.error("Secrets block [google_oauth_credentials] not found!")
        st.stop()

    client_config_dict = dict(st.secrets["google_oauth_credentials"])
    # This is the URL registered in your Google Cloud Console for the deployed app.
    cloud_redirect_uri = "https://reading-marathon.streamlit.app"

    flow = Flow.from_client_config(
        client_config={'web': client_config_dict},
        scopes=SCOPES,
        redirect_uri=cloud_redirect_uri
    )

    # Check for the authorization code from Google's redirect
    authorization_code = st.query_params.get("code")

    # Block A: Handle the redirect from Google with the authorization code.
    if authorization_code:
        try:
            # Exchange the code for credentials (access_token, refresh_token, etc.)
            flow.fetch_token(code=authorization_code)
            creds = flow.credentials
            creds_json = creds.to_json()
            creds_info = json.loads(creds_json)

            # --- CRITICAL CHECK ---
            # Google only provides a refresh_token on the *first* authorization.
            # If it's missing, the session won't be persistent.
            if 'refresh_token' not in creds_info:
                st.warning("⚠️ **إجراء مطلوب:** لم يتم استلام مفتاح التحديث اللازم للجلسة الدائمة.")
                st.info("هذا يحدث عادةً لأنك منحت الأذونات لهذا التطبيق من قبل. لإصلاح ذلك، يرجى اتباع الخطوات التالية:")
                st.markdown("""
                1.  **اذهب إلى [صفحة أذونات حساب جوجل](https://myaccount.google.com/permissions).**
                2.  ابحث عن تطبيق **"ماراثون القراءة"** في القائمة واضغط عليه.
                3.  اختر **"Remove Access"** (إزالة الدخول).
                4.  **عد إلى هنا وقم بتحديث الصفحة** لتسجيل الدخول مرة أخرى.
                """)
                st.stop()

            # If we have the refresh token, store credentials and proceed.
            st.session_state[CREDENTIALS_KEY] = creds_json
            # Clear the now-used authorization code from the URL and rerun the script.
            st.query_params.clear()
            st.rerun()

        except Exception as e:
            st.error(f"فشل في الحصول على التوكن: {e}")
            st.stop()

    # Block B: Handle an existing session.
    elif CREDENTIALS_KEY in st.session_state:
        creds_info = json.loads(st.session_state[CREDENTIALS_KEY])
        
        # This check is a safeguard. If credentials without a refresh token somehow
        # get stored, this will clear them and force re-authentication.
        if 'refresh_token' not in creds_info:
            del st.session_state[CREDENTIALS_KEY]
            st.rerun()

        creds = Credentials.from_authorized_user_info(creds_info, SCOPES)

        # If the access token is expired, use the refresh token to get a new one.
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                # Update the stored credentials with the new access token.
                st.session_state[CREDENTIALS_KEY] = creds.to_json()
            except Exception as e:
                # If refresh fails, the refresh token might be revoked. Clear session.
                st.error("انتهت صلاحية جلستك، يرجى تسجيل الدخول مرة أخرى.")
                del st.session_state[CREDENTIALS_KEY]
                st.rerun()
        
        # If credentials are valid (or have been successfully refreshed), proceed.
        if creds.valid:
            # Ensure user info is in session state
            if 'user_id' not in st.session_state:
                userinfo_service = build('oauth2', 'v2', credentials=creds)
                user_info = userinfo_service.userinfo().get().execute()
                st.session_state.user_id = user_info.get('id')
                st.session_state.user_email = user_info.get('email')
                
                # Create a workspace for the user if it's their first time.
                if not db.check_user_exists(st.session_state.user_id):
                    with st.spinner("أهلاً بك! جاري تجهيز مساحة العمل الخاصة بك لأول مرة..."):
                        db.create_new_user_workspace(st.session_state.user_id, st.session_state.user_email)
            
            return creds
        else:
            # If credentials are not valid for any other reason, clear session.
            del st.session_state[CREDENTIALS_KEY]
            st.rerun()

    # Block C: No session and no authorization code. Show the login button.
    else:
        # We request 'offline' access to get a refresh_token.
        # 'consent' prompt forces the consent screen to appear, which is crucial
        # for getting a refresh token after a user has revoked access.
        auth_url, _ = flow.authorization_url(access_type='offline', prompt='consent')
        
        st.title("🚀 أهلاً بك في \"ماراثون القراءة\"")
        st.info("للبدء، يرجى ربط حسابك في جوجل.")
        st.link_button("🔗 **الربط بحساب جوجل والبدء**", auth_url, use_container_width=True, type="primary")
        st.stop()

@st.cache_resource
def get_gspread_client(user_id: str, _creds: Credentials):
    """Create and cache gspread client."""
    if not _creds or not _creds.valid:
        st.error("🔒 **خطأ في المصادقة:** لم يتم تمرير بيانات اعتماد صالحة.")
        st.stop()
    return gspread.authorize(_creds)
