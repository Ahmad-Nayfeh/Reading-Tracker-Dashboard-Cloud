import streamlit as st
import db_manager as db
import auth_manager # <-- استيراد مدير المصادقة

st.set_page_config(
    page_title="عن التطبيق",
    page_icon="❓"
)


# This CSS snippet enforces RTL layout across the app
st.markdown("""
    <style>
        /* Main app container */
        .stApp {
            direction: rtl;
        }
        /* Sidebar */
        [data-testid="stSidebar"] {
            direction: rtl;
        }
        /* Ensure text alignment is right for various elements */
        h1, h2, h3, h4, h5, h6, p, li, .st-bk, .st-b8, .st-b9, .st-ae {
            text-align: right !important;
        }
        /* Fix for radio buttons label alignment */
        .st-b8 label {
            text-align: right !important;
            display: block;
        }
        /* Fix for selectbox label alignment */
        .st-ae label {
            text-align: right !important;
            display: block;
        }
    </style>
""", unsafe_allow_html=True)


# --- 1. UNIFIED AUTHENTICATION BLOCK ---
# هذا هو الجزء الجديد الذي يحل محل الكود القديم.
creds = auth_manager.authenticate()
user_id = st.session_state.get('user_id')
# -----------------------------------------


st.header("❓ عن التطبيق")
st.markdown("---")

# --- Load default points system for display ---
# We cache this so it doesn't reload constantly
@st.cache_data(ttl=3600)
def load_rules(user_id):
    return db.load_user_global_rules(user_id)

default_rules = load_rules(user_id)

tab1, tab2 = st.tabs(["شرح نظام التطبيق", "عن المطور والتواصل"])

with tab1:
    st.subheader("🎯 آلية عمل نظام النقاط")
    st.markdown("""
    تم تصميم هذا التطبيق لمساعدتك على إدارة تحديات القراءة وتحفيز المشاركين عبر نظام نقاط مرن.
    يمكنك تخصيص نظام النقاط الافتراضي من صفحة "الإدارة والإعدادات"، أو تعيين قوانين خاصة لكل تحدي على حدة عند إنشائه.
    """)
    
    st.info("النظام الافتراضي المطبق حالياً هو كالتالي:")

    if default_rules:
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="نقاط إنهاء الكتاب المشترك", value=f"{default_rules.get('finish_common_book_points', 0)} نقطة")
            st.metric(label="نقاط اقتباس من كتاب مشترك", value=f"{default_rules.get('quote_common_book_points', 0)} نقاط")
            st.metric(label="دقائق القراءة (مشترك) لكل نقطة", value=f"{default_rules.get('minutes_per_point_common', 0)} دقيقة")

        with col2:
            st.metric(label="نقاط حضور جلسة النقاش", value=f"{default_rules.get('attend_discussion_points', 0)} نقطة")
            st.metric(label="نقاط اقتباس من كتاب آخر", value=f"{default_rules.get('quote_other_book_points', 0)} نقطة")
            st.metric(label="دقائق القراءة (آخر) لكل نقطة", value=f"{default_rules.get('minutes_per_point_other', 0)} دقيقة")
        
        st.metric(label="نقاط إنهاء كتاب آخر", value=f"{default_rules.get('finish_other_book_points', 0)} نقطة")
    else:
        st.warning("لم يتم العثور على نظام النقاط الافتراضي.")

    st.markdown("---")
    st.subheader("⚙️ آلية عمل التطبيق")
    st.markdown("""
    1.  **الإعداد الأولي:** عند استخدام التطبيق لأول مرة، سيقوم بإنشاء جدول بيانات (Google Sheet) ونموذج (Google Form) في حسابك على جوجل.
    2.  **تسجيل القراءة:** يشارك أعضاء الفريق قراءاتهم اليومية عبر رابط نموذج جوجل الذي توفره لهم.
    3.  **مزامنة البيانات:** يقوم المشرف (أنت) بالضغط على زر "تحديث وسحب البيانات" في الشريط الجانبي. يقوم التطبيق بسحب الردود من الشيت، معالجتها، وتخزينها في قاعدة بيانات سحابية آمنة.
    4.  **التحليل والعرض:** يقوم التطبيق بعرض البيانات والإحصائيات المحدثة في لوحات التحكم المختلفة.
    """)

with tab2:
    st.subheader("🧑‍💻 عن المطور")
    st.markdown("""
    **الاسم:** احمد نايفه
    
    **الهدف من المشروع:** يهدف هذا المشروع إلى توفير أداة عصرية ومحفزة للمجموعات القرائية في الوطن العربي، للمساهمة في تعزيز ثقافة القراءة وجعلها تجربة تفاعلية وممتعة.
    
    ---
    
    ### **للتواصل والدعم الفني**
    
    إذا واجهتك أي مشكلة تقنية، أو كان لديك اقتراح لتطوير التطبيق، فلا تتردد في التواصل معي عبر أحد الحسابات التالية:

    - **البريد الإلكتروني:** [ahmadnayfeh2000@gmail.com](mailto:ahmadnayfeh2000@gmail.com)
    - **Portfolio:** [ahmadnayfeh.vercel.app](https://ahmadnayfeh.vercel.app/)
    - **LinkedIn:** [in/ahmad-nayfeh2000](https://www.linkedin.com/in/ahmad-nayfeh2000/)
    - **GitHub (للمطورين):** [Ahmad-Nayfeh](https://github.com/Ahmad-Nayfeh)
    
    يسعدني دائماً تلقي ملاحظاتكم واقتراحاتكم لجعل تجربة ماراثون القراءة أفضل للجميع.
    """)
