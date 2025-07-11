import streamlit as st
import db_manager as db
import auth_manager

st.set_page_config(
    page_title="عن التطبيق",
    page_icon="❓",
    layout="wide"
)

# This CSS snippet enforces RTL and adds custom styles for the expander component
st.markdown("""
    <style>
        /* --- Base RTL and Font Fixes --- */
        .stApp { direction: rtl; }
        [data-testid="stSidebar"] { direction: rtl; }
        h1, h2, h3, h4, h5, h6, p, li { text-align: right !important; }

        /* --- Custom Expander Styles (to look like cards) --- */
        div[data-testid="stExpander"] {
            background-color: #ffffff;
            border: 5px solid #e9ecef;
            border-radius: 12px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.05);
            margin: 5px 0;
        }

        /* Style for the expander header */
        div[data-testid="stExpander"] summary {
            font-size: 2.3em !important;
            font-weight: bold;
            color: #2c3e50;
            padding: 15px 20px;
        }
        
        /* Style for the expander content area */
        div[data-testid="stExpander"] [data-testid="stExpanderDetails"] {
            padding: 0px 25px 20px 25px;
        }

        /* --- Styles for the content inside the expander --- */
        .section-content h4 {
            color: #1a5276;
            font-size: 1.15em;
            font-weight: bold;
            margin-top: 20px;
            margin-bottom: 10px;
        }
        
        .section-content p, .section-content li {
            font-size: 1.05em !important;
            line-height: 1.8 !important;
            color: #34495e;
        }
        
        .section-content ul {
            list-style-position: outside;
            padding-right: 20px;
            margin-bottom: 15px;
        }
        
        .section-content li {
            margin-bottom: 8px;
            padding-right: 8px;
        }

        .section-content li::marker {
            color: #3498db;
            font-size: 1.1em;
        }
        
        .section-content b, .section-content strong {
            color: #21618c;
        }
        
        .contact-links a {
            text-decoration: none;
            color: #2980b9;
            font-weight: bold;
        }
        .contact-links a:hover {
            text-decoration: underline;
        }

        /* Two-column layout for Hall of Fame */
        .two-column-container {
            display: flex;
            flex-wrap: wrap;
            width: 100%;
        }
        .column {
            flex: 50%;
            padding: 0 15px;
            box-sizing: border-box;
        }
    </style>
""", unsafe_allow_html=True)


# --- UNIFIED AUTHENTICATION BLOCK ---
creds = auth_manager.authenticate()
user_id = st.session_state.get('user_id')

if not creds or not user_id:
    st.error("مصادقة المستخدم مطلوبة. يرجى العودة إلى الصفحة الرئيسية وتسجيل الدخول.")
    st.stop()
# -----------------------------------------


# --- Page Title ---
st.title("❓ عن تطبيق ماراثون القراءة")
st.markdown("<p style='font-size: 1.1em; text-align: center; color: #5D6D7E;'>أهلاً بك في الدليل الشامل! انقر على أي قسم أدناه لعرض تفاصيله.</p>", unsafe_allow_html=True)
st.divider()


# --- Section 1: Philosophy of Points ---
with st.expander("🎯 نظام المسابقات والنقاط: فلسفة التحفيز الذكي"):
    st.markdown("""
    <div class="section-content">
        <p>هذا هو قلب المشروع النابض، وهو مصمم لتحقيق توازن دقيق بين القراءة الجماعية المنظمة والقراءة الفردية الحرة، لخلق جو حماسي ومرن.</p>
        <h4>حرية الاختيار هي الأساس</h4>
        <ul>
            <li><b>مسار الكتاب المشترك:</b> يقرأ الكتاب الذي تم اختياره للتحدي. إنهاؤه يمنحه <strong>دفعة هائلة من النقاط</strong> تقديرًا لالتزامه.</li>
            <li><b>مسار الكتاب الحر:</b> يقرأ أي كتاب آخر من اختياره. هنا، تتضاعف نقاطه بناءً على <strong>وقت القراءة</strong>.</li>
        </ul>
        <h4>منطق النقاط الذكي للموازنة</h4>
        <ul>
            <li><b>للتشجيع على الالتزام:</b> نقاط إنهاء الكتاب المشترك <strong>أعلى بكثير</strong>.</li>
            <li><b>لتعزيز المشاركة المجتمعية:</b> حضور جلسة النقاش يمنح نقاطًا إضافية.</li>
            <li><b>لتشجيع القراءة العميقة:</b> إضافة <strong>اقتباس</strong> يمنح نقاطًا إضافية.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)


# --- Section 2: Hall of Fame Explained ---
with st.expander("🌟 فك شفرة الأبطال: شرح لوحة الشرف"):
    st.markdown("""
    <div class="section-content">
        <p>لوحة شرف الأبطال هي احتفاء بالإنجازات المتميزة في الماراثون. إليك معنى كل لقب:</p>
    </div>
    """, unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="section-content" style="padding: 0;">
            <ul>
                <li><b>🧠 العقل المدبّر:</b> أعلى عدد من <strong>النقاط</strong>.</li>
                <li><b>⏳ سيد الساعات:</b> أطول <strong>وقت قراءة</strong> إجمالي.</li>
                <li><b>📚 الديدان القارئ:</b> أكبر <strong>عدد من الكتب</strong> المنهَاة.</li>
                <li><b>💎 صائد الدرر:</b> أكبر عدد من <strong>الاقتباسات</strong>.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="section-content" style="padding: 0;">
            <ul>
                <li><b>🏃‍♂️ صاحب النَفَس الطويل:</b> أكبر عدد من <strong>أيام القراءة</strong>.</li>
                <li><b>⚡ العدّاء السريع:</b> أعلى قراءة في <strong>يوم واحد</strong>.</li>
                <li><b>⭐ نجم الأسبوع:</b> أعلى قراءة خلال <strong>أسبوع واحد</strong>.</li>
                <li><b>💪 عملاق الشهر:</b> أعلى قراءة خلال <strong>شهر واحد</strong>.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)


# --- Section 3: News Ticker Explained ---
with st.expander("📰 نشرة الماراثون: كيف تعمل \"آخر الأخبار\"؟"):
    st.markdown("""
    <div class="section-content">
        <p>شريط الأخبار هو نافذتك على أحدث المستجدات في الماراثون، ويعمل بطريقتين مختلفتين حسب الصفحة:</p>
        <h4>في لوحة التحكم العامة</h4>
        <ul>
            <li>يعرض الشريط هنا <strong>التغييرات التي طرأت على لوحة شرف الأبطال خلال آخر 7 أيام</strong>.</li>
            <li>الهدف هو تسليط الضوء على الديناميكية والمنافسة على مستوى الماراثون ككل.</li>
        </ul>
        <h4>في صفحة تحليلات التحديات</h4>
        <ul>
            <li>يركز الشريط هنا على <strong>أحداث التحدي المحدد فقط</strong> (مثل من أنهى الكتاب ومتى).</li>
            <li>الهدف هو متابعة التقدم والإنجازات داخل كل تحدي على حدة.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)


# --- Section 4: Q&A ---
with st.expander("🤔 أسئلة شائعة"):
    st.markdown("""
    <div class="section-content">
        <h4>كيف يتم حساب النقاط بالضبط؟</h4>
        <p>يتم حساب النقاط بناءً على نظام النقاط الافتراضي الذي يمكنك تعديله من صفحة "الإدارة والإعدادات".</p>
        <h4>هل يمكنني تعديل نظام النقاط؟</h4>
        <p>نعم! كمدير للماراثون، يمكنك الذهاب إلى "الإدارة والإعدادات" وتعديل نظام النقاط الافتراضي، أو تعيين نظام نقاط خاص لكل تحدي.</p>
        <h4>ماذا لو نسيت تسجيل قراءتي ليوم ما؟</h4>
        <p>لا تقلق. يمكن لمدير الماراثون الذهاب إلى "الإدارة والإعدادات" ثم "محرر السجلات" لتعديل أي سجل سابق. بعد الحفظ، يجب إعادة مزامنة البيانات.</p>
    </div>
    """, unsafe_allow_html=True)


# --- Section 5: About the Developer ---
with st.expander("🧑‍💻 عن المطور"):
    st.markdown("""
    <div class="section-content contact-links">
        <p><strong>الاسم:</strong> احمد نايفه</p>
        <p><strong>الهدف من المشروع:</strong> توفير أداة عصرية ومحفزة للمجموعات القرائية في الوطن العربي، لتعزيز ثقافة القراءة وجعلها تجربة تفاعلية وممتعة.</p>
        <h4><strong>للتواصل والدعم الفني</strong></h4>
        <ul>
            <li><strong>البريد الإلكتروني:</strong> <a href="mailto:ahmadnayfeh2000@gmail.com">ahmadnayfeh2000@gmail.com</a></li>
            <li><strong>Portfolio:</strong> <a href="https://ahmadnayfeh.vercel.app/" target="_blank">ahmadnayfeh.vercel.app</a></li>
            <li><strong>LinkedIn:</strong> <a href="https://www.linkedin.com/in/ahmad-nayfeh2000/" target="_blank">in/ahmad-nayfeh2000</a></li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
