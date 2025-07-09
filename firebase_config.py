import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

@st.cache_resource
def initialize_firebase_app():
    """
    Initializes the Firebase Admin SDK using st.secrets.
    This works for both local development (with .streamlit/secrets.toml)
    and Streamlit Cloud deployment.
    """
    try:
        # Check if the app is already initialized
        if not firebase_admin._apps:
            # st.secrets automatically reads from the secrets.toml file locally
            if "firebase_credentials" in st.secrets:
                creds_dict = dict(st.secrets["firebase_credentials"])
                cred = credentials.Certificate(creds_dict)
                firebase_admin.initialize_app(cred)
            else:
                st.error("🔥 خطأ: لم يتم العثور على إعدادات `firebase_credentials` في ملف الأسرار (secrets.toml).")
                st.stop()
        
        return firestore.client()
    except Exception as e:
        st.error(f"🔥 خطأ في تهيئة Firebase: {e}")
        st.stop()

# Initialize the database client
db = initialize_firebase_app()
