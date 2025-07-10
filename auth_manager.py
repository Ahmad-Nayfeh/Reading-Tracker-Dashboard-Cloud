import streamlit as st
import gspread
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
import db_manager as db
from googleapiclient.discovery import build
import os
import json

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
    try:
        # This is the most reliable way to check for Streamlit Cloud
        from streamlit.runtime.get_instance import get_instance
        from streamlit.runtime.scriptrunner.script_run_context import get_script_run_ctx
        ctx = get_script_run_ctx()
        is_cloud = 'streamlit.app' in ctx.query_string
    except (ImportError, AttributeError):
        # Fallback for older versions or different environments
        is_cloud = "STREAMLIT_SERVER_ADDRESS" in os.environ

    creds_dict = dict(st.secrets["google_oauth_credentials"])
    redirect_uris = creds_dict.get('redirect_uris', [])

    if is_cloud:
        uri = next((uri for uri in redirect_uris if 'streamlit.app' in uri), None)
        if uri: return uri
    
    # Default to localhost if not on cloud or if cloud URI not found
    return next((uri for uri in redirect_uris if 'localhost' in uri), redirect_uris[0] if redirect_uris else None)


def authenticate():
    """
    Handles the complete authentication flow using st.session_state for persistence.
    This method is robust against page reloads and works on Streamlit Cloud.
    """
    # Check if secrets are configured
    if "google_oauth_credentials" not in st.secrets:
        st.error("🔑 **خطأ في الإعدادات:** لم يتم العثور على `google_oauth_credentials` في ملف الأسرار.")
        st.stop()

    creds_dict = dict(st.secrets["google_oauth_credentials"])
    redirect_uri = get_redirect_uri()

    if not redirect_uri:
        st.error("🔑 **خطأ في الإعدادات:** لم يتم العثور على `redirect_uri` مناسب في ملف الأسرار.")
        st.stop()

    # Create the Flow instance
    flow = Flow.from_client_config(
        client_config={'web': creds_dict},
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )

    # Check for authorization code in URL
    authorization_code = st.query_params.get("code")

    # If code is in the URL, this is the callback from Google
    if authorization_code and not st.session_state.get('authed_from_code'):
        try:
            flow.fetch_token(code=authorization_code)
            creds = flow.credentials
            # Store the credentials as a JSON string in the session state
            st.session_state.credentials_json = creds.to_json()
            # A flag to prevent re-authenticating from the same code
            st.session_state.authed_from_code = True 
            # Clear the query params and rerun to clean the URL
            st.query_params.clear()
            st.rerun()
        except Exception as e:
            st.error(f"فشل في الحصول على التوكن: {e}")
            st.stop()

    # If credentials are in the session state, use them
    elif 'credentials_json' in st.session_state:
        creds_info = json.loads(st.session_state.credentials_json)
        creds = Credentials.from_authorized_user_info(creds_info, SCOPES)

        # Refresh the token if it's expired
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                # Update the session state with the refreshed credentials
                st.session_state.credentials_json = creds.to_json()
            except Exception as e:
                st.error("انتهت صلاحية جلستك، يرجى تسجيل الدخول مرة أخرى.")
                # Clear the faulty credentials and rerun
                del st.session_state.credentials_json
                st.rerun()
        
        # If credentials are valid, populate user info and return
        if creds.valid:
            if 'user_id' not in st.session_state:
                userinfo_service = build('oauth2', 'v2', credentials=creds)
                user_info = userinfo_service.userinfo().get().execute()
                st.session_state.user_id = user_info.get('id')
                st.session_state.user_email = user_info.get('email')
                # Create workspace if it's the first time for this user
                if not db.check_user_exists(st.session_state.user_id):
                    with st.spinner("أهلاً بك! جاري تجهيز مساحة العمل الخاصة بك لأول مرة..."):
                        db.create_new_user_workspace(st.session_state.user_id, st.session_state.user_email)
            
            # Store the live credentials object for other functions to use
            st.session_state.credentials = creds
            return creds

    # If no credentials and no code, show the login button
    else:
        auth_url, _ = flow.authorization_url(prompt='consent')
        st.title("🚀 أهلاً بك في \"ماراثون القراءة\"")
        st.info("للبدء، يرجى ربط حسابك في جوجل. سيقوم التطبيق بإنشاء مساحة عمل سحابية خاصة بك لإدارة تحديات القراءة بكل سهولة.")
        st.link_button("🔗 **الربط بحساب جوجل والبدء**", auth_url, use_container_width=True, type="primary")
        st.stop()


@st.cache_resource
def get_gspread_client(user_id: str, _creds: Credentials):
    """
    Creates a unique gspread client for each user.
    """
    if not _creds or not _creds.valid:
        st.error("🔒 **خطأ في المصادقة:** لم يتم تمرير بيانات اعتماد صالحة.")
        st.stop()
    return gspread.authorize(_creds)
