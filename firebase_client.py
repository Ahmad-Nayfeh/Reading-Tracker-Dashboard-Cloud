import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import os

# --- Constants ---
SERVICE_ACCOUNT_FILE = 'firebase_service_account.json'

def initialize_firebase():
    """
    Initializes the Firebase Admin SDK using a service account,
    ensuring it's only done once per session.
    Returns the Firestore database client.
    """
    # Check if Firebase app has already been initialized in the current session
    if not firebase_admin._apps:
        try:
            # Check if the service account file exists
            if not os.path.exists(SERVICE_ACCOUNT_FILE):
                st.error(f"خطأ حرج: لم يتم العثور على ملف مفتاح الخدمة '{SERVICE_ACCOUNT_FILE}'. يرجى التأكد من وجوده في المجلد الرئيسي للمشروع.")
                st.stop()
            
            # Initialize the app with a service account, granting admin privileges
            cred = credentials.Certificate(SERVICE_ACCOUNT_FILE)
            firebase_admin.initialize_app(cred)
            
        except Exception as e:
            st.error(f"فشل في تهيئة Firebase: {e}")
            st.stop()
            
    # Return the Firestore database client
    return firestore.client()

# Use Streamlit's cache_resource to get a singleton instance of the db client.
# This is the modern, recommended way to handle persistent connections.
@st.cache_resource
def get_db_client():
    """
    Returns a cached instance of the Firestore database client.
    """
    return initialize_firebase()

# --- Example Usage (for testing purposes) ---
if __name__ == '__main__':
    # This block will only run when you execute `python firebase_client.py` directly
    db = get_db_client()
    print("✅ Firebase connection successful!")
    print(f"Firestore client object: {db}")