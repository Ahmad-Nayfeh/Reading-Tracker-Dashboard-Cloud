import streamlit as st
import gspread
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
import db_manager as db
from googleapiclient.discovery import build
import os
import json
import hashlib
import time
from datetime import datetime, timedelta

# The scopes required by the application.
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/forms.body",
    "openid",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email"
]

def _get_user_session_key(user_id: str) -> str:
    """Generate a unique session key for the user"""
    return f"user_session_{hashlib.md5(user_id.encode()).hexdigest()}"

def _store_credentials_persistent(user_id: str, creds_json: str):
    """Store credentials in a way that persists across page refreshes"""
    session_key = _get_user_session_key(user_id)
    
    # Store in multiple places for redundancy
    st.session_state[f'creds_{user_id}'] = creds_json
    st.session_state['current_user_creds'] = creds_json
    st.session_state['auth_timestamp'] = time.time()
    
    # Use query params as a backup persistence mechanism
    if 'auth_session' not in st.query_params:
        st.query_params['auth_session'] = session_key[:16]  # Shortened for URL cleanliness

def _retrieve_credentials_persistent(user_id: str) -> str:
    """Retrieve stored credentials from various sources"""
    # Try multiple sources in order of preference
    sources = [
        st.session_state.get(f'creds_{user_id}'),
        st.session_state.get('current_user_creds'),
        st.session_state.get('credentials_json')  # Legacy support
    ]
    
    for creds_json in sources:
        if creds_json:
            return creds_json
    
    return None

def _is_session_valid() -> bool:
    """Check if the current session is still valid"""
    auth_timestamp = st.session_state.get('auth_timestamp')
    if not auth_timestamp:
        return False
    
    # Session expires after 1 hour of inactivity
    return (time.time() - auth_timestamp) < 3600

def _clear_all_auth_data():
    """Clear all authentication data from session"""
    keys_to_remove = [
        'credentials_json', 'current_user_creds', 'auth_timestamp',
        'user_id', 'user_email', 'google_oauth_credentials'
    ]
    
    for key in keys_to_remove:
        if key in st.session_state:
            del st.session_state[key]
    
    # Also clear user-specific credential keys
    keys_to_check = list(st.session_state.keys())
    for key in keys_to_check:
        if key.startswith('creds_'):
            del st.session_state[key]
    
    # Clear query params
    if 'auth_session' in st.query_params:
        del st.query_params['auth_session']

def authenticate():
    """
    Handles the complete Google OAuth 2.0 flow with robust session persistence
    and error handling. This version survives page refreshes.
    """
    
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
        st.info("🔄 جاري معالجة تسجيل الدخول...")
        try:
            flow.fetch_token(code=authorization_code)
            creds_json = flow.credentials.to_json()
            
            # Get user info immediately to establish session
            userinfo_service = build('oauth2', 'v2', credentials=flow.credentials)
            user_info = userinfo_service.userinfo().get().execute()
            user_id = user_info.get('id')
            user_email = user_info.get('email')
            
            # Store credentials persistently
            _store_credentials_persistent(user_id, creds_json)
            
            # Store user info
            st.session_state.user_id = user_id
            st.session_state.user_email = user_email
            
            # Check if user exists in database
            if not db.check_user_exists(user_id):
                with st.spinner("أهلاً بك! جاري تجهيز مساحة العمل الخاصة بك لأول مرة..."):
                    db.create_new_user_workspace(user_id, user_email)
            
            # Clear the authorization code from URL
            st.query_params.clear()
            st.query_params['auth_session'] = _get_user_session_key(user_id)[:16]
            st.rerun()
            
        except Exception as e:
            st.error(f"فشل في تسجيل الدخول: {e}")
            _clear_all_auth_data()
            st.stop()

    # Block B: Handle existing session (this is where the magic happens for persistence)
    elif 'user_id' in st.session_state and _is_session_valid():
        user_id = st.session_state.user_id
        creds_json = _retrieve_credentials_persistent(user_id)
        
        if creds_json:
            try:
                creds_info = json.loads(creds_json)
                
                # Check for refresh token
                if 'refresh_token' not in creds_info:
                    st.warning("⚠️ انتهت صلاحية الجلسة. يرجى تسجيل الدخول مرة أخرى.")
                    _clear_all_auth_data()
                    st.rerun()
                    return None
                
                creds = Credentials.from_authorized_user_info(creds_info, SCOPES)
                
                # Handle expired credentials
                if creds.expired and creds.refresh_token:
                    try:
                        creds.refresh(Request())
                        # Update stored credentials
                        updated_creds_json = creds.to_json()
                        _store_credentials_persistent(user_id, updated_creds_json)
                        st.session_state['auth_timestamp'] = time.time()  # Reset timestamp
                        
                    except Exception as e:
                        st.error("انتهت صلاحية جلستك، يرجى تسجيل الدخول مرة أخرى.")
                        _clear_all_auth_data()
                        st.rerun()
                        return None
                
                if creds.valid:
                    return creds
                else:
                    _clear_all_auth_data()
                    st.rerun()
                    return None
                    
            except Exception as e:
                st.error(f"خطأ في معالجة بيانات المصادقة: {e}")
                _clear_all_auth_data()
                st.rerun()
                return None
        else:
            _clear_all_auth_data()
            st.rerun()
            return None

    # Block C: Check for existing auth session from URL params
    elif 'auth_session' in st.query_params:
        st.info("🔄 جاري استعادة الجلسة...")
        # This indicates a page refresh - try to restore session
        # Since we can't store credentials in URL, we'll need to re-authenticate
        st.query_params.clear()
        st.info("تم تحديث الصفحة. يرجى تسجيل الدخول مرة أخرى.")
        time.sleep(2)
        st.rerun()

    # Block D: Show login button if no authentication is found
    else:
        auth_url, _ = flow.authorization_url(access_type='offline', prompt='consent')
        
        st.title("🚀 أهلاً بك في \"ماراثون القراءة\"")
        st.info("للبدء، يرجى ربط حسابك في جوجل.")
        
        # Add logout button if there's any stale session data
        if any(key in st.session_state for key in ['user_id', 'user_email', 'credentials_json']):
            if st.button("🔄 مسح البيانات المؤقتة", type="secondary"):
                _clear_all_auth_data()
                st.rerun()
        
        st.link_button("🔗 **الربط بحساب جوجل والبدء**", auth_url, use_container_width=True, type="primary")
        st.stop()

    return None


@st.cache_resource
def get_gspread_client(user_id: str, _creds: Credentials):
    """Create and cache gspread client"""
    if not _creds or not _creds.valid:
        st.error("🔒 **خطأ في المصادقة:** لم يتم تمرير بيانات اعتماد صالحة.")
        st.stop()
    return gspread.authorize(_creds)


def logout():
    """Completely log out the user"""
    _clear_all_auth_data()
    st.success("تم تسجيل الخروج بنجاح!")
    time.sleep(1)
    st.rerun()


def get_current_user_info():
    """Get current user information if authenticated"""
    if 'user_id' in st.session_state and _is_session_valid():
        return {
            'user_id': st.session_state.user_id,
            'user_email': st.session_state.user_email,
            'authenticated': True
        }
    return {'authenticated': False}