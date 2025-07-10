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
    # هذه الطريقة أكثر موثوقية للتحقق من بيئة Streamlit Cloud
    is_cloud = "STREAMLIT_SERVER_ADDRESS" in os.environ

    creds_dict = dict(st.secrets["google_oauth_credentials"])
    redirect_uris = creds_dict.get('redirect_uris', [])

    if is_cloud:
        # ابحث عن الرابط الذي يحتوي على 'streamlit.app'
        uri = next((uri for uri in redirect_uris if 'streamlit.app' in uri), None)
        if uri:
            return uri
        else:
            # في حال لم يجد الرابط السحابي في ملف الأسرار لسبب ما
            st.error("لم يتم العثور على رابط التوجيه (redirect URI) الخاص بالنسخة السحابية في إعداداتك.")
            st.stop()

    # إذا لم يكن على السحابة، استخدم الرابط المحلي
    return next((uri for uri in redirect_uris if 'localhost' in uri), None)


# The updated authenticate function
def authenticate():
    """
    Handles the complete authentication flow using st.session_state for persistence.
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

    # This is the correct logical order:
    # 1. Handle the authorization code from Google first.
    if authorization_code:
        try:
            flow.fetch_token(code=authorization_code)
            creds = flow.credentials
            st.session_state.credentials_json = creds.to_json()
            # Clear the query params from the URL and rerun the script.
            st.query_params.clear()
            st.rerun()
        except Exception as e:
            st.error(f"فشل في الحصول على التوكن: {e}")
            st.stop()

    # 2. If no code, check if credentials are in the session state.
    elif 'credentials_json' in st.session_state:
        creds_info = json.loads(st.session_state.credentials_json)
        creds = Credentials.from_authorized_user_info(creds_info, SCOPES)

        # Refresh the token if it's expired
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                st.session_state.credentials_json = creds.to_json()
            except Exception as e:
                st.error("انتهت صلاحية جلستك، يرجى تسجيل الدخول مرة أخرى.")
                del st.session_state.credentials_json
                st.rerun()
        
        # If credentials are valid, populate user info and return
        if creds.valid:
            if 'user_id' not in st.session_state:
                userinfo_service = build('oauth2', 'v2', credentials=creds)
                user_info = userinfo_service.userinfo().get().execute()
                st.session_state.user_id = user_info.get('id')
                st.session_state.user_email = user_info.get('email')
                if not db.check_user_exists(st.session_state.user_id):
                    with st.spinner("أهلاً بك! جاري تجهيز مساحة العمل الخاصة بك لأول مرة..."):
                        db.create_new_user_workspace(st.session_state.user_id, st.session_state.user_email)
            
            st.session_state.credentials = creds
            return creds

    # 3. If no code and no credentials, show the login button.
    else:
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

