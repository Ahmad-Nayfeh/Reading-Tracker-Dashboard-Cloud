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

CREDENTIALS_KEY = 'credentials_json_persistent'

def authenticate():
    """
    A diagnostic-heavy version of the authentication flow.
    It rigorously checks for the refresh_token and provides clear feedback.
    """
    st.warning("--- DEBUG: `authenticate()` function has been called. ---")

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

    # Block A: Handle the redirect from Google with the authorization code.
    if authorization_code:
        st.warning("--- DEBUG: Block A - Authorization code found in URL. ---")
        try:
            st.warning("--- DEBUG: Fetching token from Google... ---")
            flow.fetch_token(code=authorization_code)
            creds = flow.credentials
            creds_json = creds.to_json()
            creds_info = json.loads(creds_json)

            # --- CRITICAL DIAGNOSTIC CHECK ---
            if 'refresh_token' not in creds_info:
                st.error("### 🔴 فشل المصادقة: لم يتم استلام مفتاح الجلسة الدائمة (Refresh Token)")
                st.warning("هذا هو السبب الجذري للمشكلة. يحدث هذا عادةً لأنك منحت الأذونات لهذا التطبيق في الماضي.")
                st.info("لإصلاح ذلك بشكل نهائي، يرجى اتباع الخطوات التالية بدقة:")
                st.markdown("""
                1.  **اذهب إلى صفحة أذونات حساب جوجل عبر هذا الرابط: [https://myaccount.google.com/permissions](https://myaccount.google.com/permissions)**
                2.  في قائمة "Third-party apps with account access"، ابحث عن تطبيق **"ماراثون القراءة"** واضغط عليه.
                3.  اختر **"REMOVE ACCESS"** (إزالة الدخول) وقم بالتأكيد.
                4.  بعد إزالة الوصول، **عد إلى هنا وقم بتحديث هذه الصفحة (F5)** للمحاولة مرة أخرى.
                """)
                st.stop()

            st.warning("--- DEBUG: SUCCESS! Refresh token received. Storing credentials in session state. ---")
            st.session_state[CREDENTIALS_KEY] = creds_json
            st.query_params.clear()
            st.warning("--- DEBUG: Rerunning script after storing credentials. ---")
            st.rerun()

        except Exception as e:
            st.error(f"--- DEBUG: Exception in Block A: {e} ---")
            st.stop()

    # Block B: Handle an existing session.
    elif CREDENTIALS_KEY in st.session_state:
        st.warning(f"--- DEBUG: Block B - Found `{CREDENTIALS_KEY}` in session state. Processing existing session. ---")
        creds_info = json.loads(st.session_state[CREDENTIALS_KEY])
        
        if 'refresh_token' not in creds_info:
            st.warning("--- DEBUG: CRITICAL! Stored credentials are incomplete (missing refresh_token). Clearing session. ---")
            del st.session_state[CREDENTIALS_KEY]
            st.rerun()

        creds = Credentials.from_authorized_user_info(creds_info, SCOPES)

        if creds.expired and creds.refresh_token:
            st.warning("--- DEBUG: Credentials expired. Attempting to refresh... ---")
            try:
                creds.refresh(Request())
                st.session_state[CREDENTIALS_KEY] = creds.to_json()
                st.warning("--- DEBUG: Refresh successful. ---")
            except Exception as e:
                st.warning(f"--- DEBUG: Refresh token failed: {e}. Clearing session. ---")
                del st.session_state[CREDENTIALS_KEY]
                st.rerun()
        
        if creds.valid:
            st.warning("--- DEBUG: Credentials are valid. Authentication successful. ---")
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
            st.warning("--- DEBUG: Credentials are not valid for an unknown reason. Clearing session. ---")
            del st.session_state[CREDENTIALS_KEY]
            st.rerun()

    # Block C: No session and no authorization code. Show the login button.
    else:
        st.warning("--- DEBUG: Block C - No credentials in session and no auth code in URL. Displaying login button. ---")
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
