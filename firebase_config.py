import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import os

@st.cache_resource
def initialize_firebase_app():
    """
    Initializes the Firebase Admin SDK using Streamlit Secrets for deployment,
    or a local file for local development.
    """
    try:
        if not firebase_admin._apps:
            # التحقق مما إذا كنا نعمل على Streamlit Cloud
            if 'firebase_credentials' in st.secrets:
                creds_dict = dict(st.secrets["firebase_credentials"])
                cred = credentials.Certificate(creds_dict)
            else:
                # الوضع المحلي يعمل كما هو
                SERVICE_ACCOUNT_FILE = 'firebase_service_account.json'
                if not os.path.exists(SERVICE_ACCOUNT_FILE):
                    st.error(f"🔑 ملف '{SERVICE_ACCOUNT_FILE}' غير موجود. يرجى التأكد من وجوده محلياً.")
                    st.stop()
                cred = credentials.Certificate(SERVICE_ACCOUNT_FILE)
            
            firebase_admin.initialize_app(cred)
        
        return firestore.client()
    except Exception as e:
        st.error(f"🔥 خطأ في تهيئة Firebase: {e}")
        st.stop()

db = initialize_firebase_app()