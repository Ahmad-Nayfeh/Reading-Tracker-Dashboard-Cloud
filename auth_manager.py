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
    This is the most critical function for cloud deployment to work correctly.
    """
    # This is the reliable way to check if the app is running on Streamlit Cloud.
    # It checks for an environment variable that Streamlit Cloud sets automatically.
    if "STREAMLIT_SERVER_ADDRESS" in os.environ:
        # On Streamlit Cloud, the URI is the app's main URL.
        # Make sure this URL exactly matches the one in your Google Cloud Console.
        return "https://reading-marathon.streamlit.app"
    else:
        # For local development, the URI is localhost with the default port.
        return "http://localhost:8501"

def authenticate():
    """
    Handles the complete Google OAuth 2.0 flow using st.session_state for persistence.
    This function is designed to work seamlessly both locally and on Streamlit Cloud.
    """
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

    # Check for the authorization code returned by Google in the URL query parameters.
    authorization_code = st.query_params.get("code")

    # --- Authentication Flow Logic ---

    # Step 1: If an authorization code is present in the URL, exchange it for credentials.
    if authorization_code:
        try:
            # Exchange the code for a token.
            flow.fetch_token(code=authorization_code)
            # Store the credentials securely in the session state as a JSON string.
            st.session_state.credentials_json = flow.credentials.to_json()
            # Clear the query parameters from the URL to have a clean address.
            st.query_params.clear()
            # Rerun the script to process the new state (now with credentials).
            st.rerun()
        except Exception as e:
            st.error(f"فشل في الحصول على التوكن: {e}")
            st.stop()

    # Step 2: If no code, but credentials exist in the session state, use them.
    elif 'credentials_json' in st.session_state:
        creds_info = json.loads(st.session_state.credentials_json)
        creds = Credentials.from_authorized_user_info(creds_info, SCOPES)

        # If the token is expired, refresh it using the refresh token.
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                # Update the session state with the refreshed credentials.
                st.session_state.credentials_json = creds.to_json()
            except Exception as e:
                # If refresh fails, the user must log in again.
                st.error("انتهت صلاحية جلستك، يرجى تسجيل الدخول مرة أخرى.")
                del st.session_state.credentials_json
                st.rerun()
        
        # If credentials are valid (or were successfully refreshed), proceed.
        if creds.valid:
            # Populate user info if it's not already in the session state.
            if 'user_id' not in st.session_state:
                userinfo_service = build('oauth2', 'v2', credentials=creds)
                user_info = userinfo_service.userinfo().get().execute()
                st.session_state.user_id = user_info.get('id')
                st.session_state.user_email = user_info.get('email')
                
                # Check if it's a new user and create their workspace in Firestore.
                if not db.check_user_exists(st.session_state.user_id):
                    with st.spinner("أهلاً بك! جاري تجهيز مساحة العمل الخاصة بك لأول مرة..."):
                        db.create_new_user_workspace(st.session_state.user_id, st.session_state.user_email)
            
            # Return the valid credentials object for the app to use.
            return creds

    # Step 3: If no code and no credentials, display the login button to the user.
    else:
        # Generate the authorization URL.
        # 'access_type='offline'' is crucial to get a refresh token for long-lived sessions.
        auth_url, _ = flow.authorization_url(access_type='offline', prompt='consent')
        
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
