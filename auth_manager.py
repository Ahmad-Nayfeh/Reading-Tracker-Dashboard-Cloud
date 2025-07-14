import streamlit as st
import gspread
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
import db_manager as db
from googleapiclient.discovery import build
import json
import time
import requests

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
    if "google_oauth_credentials" not in st.secrets:
        st.error("Secrets block [google_oauth_credentials] not found!")
        st.stop()
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
    refresh_token = db.get_refresh_token(user_id)
    if not refresh_token:
        return None

    client_config = dict(st.secrets["google_oauth_credentials"])
    try:
        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri='https://oauth2.googleapis.com/token',
            client_id=client_config.get("client_id"),
            client_secret=client_config.get("client_secret"),
            scopes=SCOPES
        )
        creds.refresh(Request())
        return creds
    except Exception:
        return None

def authenticate():
    """
    Handles the complete Google OAuth 2.0 flow with Firestore-backed persistence
    and self-healing URL parameters to survive page refreshes and navigation.
    """
    # Priority 1: Check for valid credentials in the current session state.
    if SESSION_STATE_KEY in st.session_state:
        creds = Credentials.from_authorized_user_info(json.loads(st.session_state[SESSION_STATE_KEY]))
        if creds.valid:
            if 'user_id' not in st.query_params and 'user_id' in st.session_state:
                st.query_params['user_id'] = st.session_state.get('user_id')
            return creds
        elif creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                st.session_state[SESSION_STATE_KEY] = creds.to_json()
                if 'user_id' not in st.query_params and 'user_id' in st.session_state:
                    st.query_params['user_id'] = st.session_state.get('user_id')
                return creds
            except Exception:
                del st.session_state[SESSION_STATE_KEY]

    # Priority 2: Handle the redirect from Google's login screen (has `code`).
    authorization_code = st.query_params.get("code")
    if authorization_code:
        flow = _get_flow()
        try:
            # --- المحاولة الأولى لجلب التوكن ---
            flow.fetch_token(code=authorization_code)
            creds = flow.credentials

        except Exception as e:
            # --- التعامل الذكي مع خطأ "المنحة غير صالحة" ---
            if 'invalid_grant' in str(e):
                st.error("⚠️ يبدو أنك قمت بإلغاء صلاحيات التطبيق مؤخراً.")
                st.info("لا تقلق، سنحاول إعادة طلب الموافقة من جديد. يرجى الضغط على الزر أدناه للمتابعة.")

                # نعيد بناء رابط المصادقة مع معلمات تجبر على إعادة الموافقة
                auth_url, _ = flow.authorization_url(
                    access_type='offline', 
                    prompt='consent', 
                    include_granted_scopes='true'
                )

                st.link_button("🔗 إعادة الربط بحساب جوجل (مهم)", auth_url, use_container_width=True, type="primary")
                st.stop() # نوقف التنفيذ وننتظر من المستخدم الضغط على الرابط الجديد
            else:
                # لأي أخطاء أخرى، نعرض الخطأ كما هو
                st.error(f"حدث خطأ غير متوقع أثناء المصادقة: {e}")
                st.stop()


        if not creds.refresh_token:
            st.error("### 🔴 فشل المصادقة: لم يتم استلام مفتاح الجلسة الدائمة")
            st.info("لإصلاح ذلك، يرجى إلغاء وصول التطبيق من إعدادات حسابك في جوجل ثم المحاولة مرة أخرى.")
            st.markdown("[رابط صفحة أذونات حساب جوجل](https://myaccount.google.com/permissions)")
            st.stop()

        userinfo_service = build('oauth2', 'v2', credentials=creds)
        user_info = userinfo_service.userinfo().get().execute()
        user_id = user_info.get('id')
        user_email = user_info.get('email')

        if not db.check_user_exists(user_id):
            db.create_new_user_workspace(user_id, user_email)

        db.save_refresh_token(user_id, creds.refresh_token)

        st.session_state.user_id = user_id
        st.session_state.user_email = user_email
        st.session_state[SESSION_STATE_KEY] = creds.to_json()

        st.query_params.clear()
        st.query_params['user_id'] = user_id
        st.rerun()

    # Priority 3: Handle F5 refresh by checking for `user_id` in URL params.
    user_id_from_params = st.query_params.get("user_id")
    if user_id_from_params:
        creds = _rebuild_credentials_from_db(user_id_from_params)
        if creds and creds.valid:
            userinfo_service = build('oauth2', 'v2', credentials=creds)
            user_info = userinfo_service.userinfo().get().execute()
            st.session_state.user_id = user_info.get('id')
            st.session_state.user_email = user_info.get('email')
            st.session_state[SESSION_STATE_KEY] = creds.to_json()
            st.rerun()

    # Priority 4: If all else fails, show the login button.
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

def logout():
    """
    Clears all session information, logs the user out, and clears URL params.
    """
    keys_to_delete = [SESSION_STATE_KEY, 'user_id', 'user_email']
    for key in keys_to_delete:
        if key in st.session_state:
            del st.session_state[key]
    
    # Use a loop to clear all query params, especially user_id
    query_params = st.query_params.to_dict()
    if query_params:
        st.query_params.clear()

    st.success("تم تسجيل الخروج بنجاح. جارٍ إعادة التوجيه...")
    time.sleep(2)
    st.rerun()



def revoke_google_token(refresh_token: str):
    """
    Revokes a Google refresh token, effectively logging the user out of the app's access.
    """
    if not refresh_token:
        return False, "No refresh token provided."
    try:
        response = requests.post('https://oauth2.googleapis.com/revoke',
            params={'token': refresh_token},
            headers={'content-type': 'application/x-www-form-urlencoded'})

        return response.status_code == 200, response.status_code
    except Exception as e:
        return False, str(e)