import streamlit as st
import gspread
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
import db_manager as db
from googleapiclient.discovery import build

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
        from streamlit.web.server.server import Server
        # When running on Streamlit Cloud, the server address will contain 'streamlit.app'
        is_cloud = "streamlit.app" in Server.get_current()._get_server_address_for_browser()
    except (ImportError, AttributeError):
        # Fallback for different environments or streamlit versions, assume local
        is_cloud = False

    creds_dict = dict(st.secrets["google_oauth_credentials"])
    redirect_uris = creds_dict.get('redirect_uris', [])

    if is_cloud:
        return next((uri for uri in redirect_uris if 'streamlit.app' in uri), None)
    else:
        return next((uri for uri in redirect_uris if 'localhost' in uri), redirect_uris[0] if redirect_uris else None)


def authenticate():
    """
    Handles the authentication flow using st.secrets for configuration.
    It prioritizes credentials stored in the current session.
    """
    # Priority 1: Check for valid credentials in the current session state
    if 'credentials' in st.session_state and st.session_state.credentials.valid:
        return st.session_state.credentials

    # Check if secrets are configured
    if "google_oauth_credentials" not in st.secrets:
        st.error("🔑 **خطأ في الإعدادات:** لم يتم العثور على `google_oauth_credentials` في ملف الأسرار (secrets.toml).")
        st.stop()

    # Configure the OAuth flow using st.secrets
    creds_dict = dict(st.secrets["google_oauth_credentials"])
    redirect_uri = get_redirect_uri()

    if not redirect_uri:
        st.error("🔑 **خطأ في الإعدادات:** لم يتم العثور على `redirect_uri` مناسب في ملف الأسرار (secrets.toml).")
        st.stop()

    flow = Flow.from_client_config(
        client_config={'web': creds_dict},
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )
    
    # Check for the authorization code in the URL query parameters
    authorization_code = st.query_params.get("code")
    
    if authorization_code:
        # If we have a code, fetch the token
        flow.fetch_token(code=authorization_code)
        creds = flow.credentials
        
        # Store credentials in the session state
        st.session_state.credentials = creds
        
        # Get user info and set up the workspace if it's the first time
        try:
            userinfo_service = build('oauth2', 'v2', credentials=creds)
            user_info = userinfo_service.userinfo().get().execute()
            
            user_id = user_info.get('id')
            user_email = user_info.get('email')

            if not user_id or not user_email:
                st.error("لم نتمكن من الحصول على معرّف المستخدم من جوجل. يرجى المحاولة مرة أخرى.")
                st.stop()

            st.session_state.user_id = user_id
            st.session_state.user_email = user_info.get('email')

            if not db.check_user_exists(user_id):
                with st.spinner("أهلاً بك! جاري تجهيز مساحة العمل الخاصة بك لأول مرة..."):
                    db.create_new_user_workspace(user_id, user_email)
            
        except Exception as e:
            st.error(f"حدث خطأ أثناء الحصول على معلومات المستخدم أو إنشاء مساحة العمل: {e}")
            st.stop()
        
        # Clear the query parameters from the URL and rerun the app
        st.query_params.clear()
        st.rerun()
    
    else:
        # If there are no credentials and no code, show the login button
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
