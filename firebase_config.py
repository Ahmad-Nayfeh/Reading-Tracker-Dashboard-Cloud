import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

# --- Constants ---
SERVICE_ACCOUNT_FILE = 'firebase_service_account.json'

@st.cache_resource
def initialize_firebase_app():
    """
    Initializes the Firebase Admin SDK using a service account.
    Uses Streamlit's caching to ensure this function runs only once.

    Returns:
        firestore.Client: An instance of the Firestore client.
    """
    try:
        # التحقق مما إذا كان التطبيق قد تم تهيئته بالفعل
        if not firebase_admin._apps:
            # تهيئة التطبيق باستخدام ملف حساب الخدمة
            cred = credentials.Certificate(SERVICE_ACCOUNT_FILE)
            firebase_admin.initialize_app(cred)
        
        # إرجاع عميل Firestore للتفاعل مع قاعدة البيانات
        return firestore.client()
    except FileNotFoundError:
        # في حالة عدم العثور على ملف المفتاح، يتم عرض رسالة خطأ واضحة للمستخدم
        st.error(f"🔑 **خطأ فادح:** لم يتم العثور على ملف حساب خدمة Firebase '{SERVICE_ACCOUNT_FILE}'. يرجى التأكد من وجود الملف في المجلد الرئيسي للمشروع.")
        st.stop() # إيقاف تشغيل التطبيق لأن الاتصال بقاعدة البيانات ضروري
    except Exception as e:
        # التعامل مع أي أخطاء أخرى قد تحدث أثناء التهيئة
        st.error(f"🔥 **خطأ في تهيئة Firebase:** حدث خطأ غير متوقع. التفاصيل: {e}")
        st.stop()

# تهيئة التطبيق والحصول على عميل قاعدة البيانات
# سيتم استيراد هذا المتغير 'db' في الملفات الأخرى للوصول إلى Firestore
db = initialize_firebase_app()
