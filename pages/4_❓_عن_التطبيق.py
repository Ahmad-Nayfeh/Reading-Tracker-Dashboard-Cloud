import streamlit as st
import db_manager as db
import auth_manager

st.set_page_config(
    page_title="عن التطبيق",
    page_icon="❓",
    layout="wide"
)

# This CSS snippet enforces RTL and adds custom styles for the new card-based layout
st.markdown("""
    <style>
        /* --- Base RTL and Font Fixes --- */
        .stApp { direction: rtl; }
        [data-testid="stSidebar"] { direction: rtl; }
        h1, h2, h3, h4, h5, h6, p, li { text-align: right !important; }

        /* --- Custom Section Card Styles --- */
        .section-card {
            background-color: #ffffff;
            border: 1px solid #e9ecef;
            border-radius: 12px;
            padding: 25px 30px;
            margin: 25px 0;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.05);
        }
        
        .section-header {
            display: flex;
            align-items: center;
            justify-content: flex-start;
            border-bottom: 2px solid #f0f2f6;
            padding-bottom: 15px;
            margin-bottom: 20px;
        }
        
        .section-header .icon {
            font-size: 2.2em;
            margin-left: 15px;
            color: #2980b9;
        }
        
        .section-header h2 {
            font-size: 1.8em;
            font-weight: bold;
            color: #2c3e50;
            margin: 0;
        }
        
        .section-content h4 {
            color: #1a5276;
            font-size: 1.3em;
            font-weight: bold;
            margin-top: 25px;
            margin-bottom: 15px;
        }
        
        .section-content p, .section-content li {
            font-size: 1.15em !important;
            line-height: 2 !important;
            color: #34495e;
        }
        
        .section-content ul {
            list-style-position: outside;
            padding-right: 25px;
            margin: 0;
        }
        
        .section-content li {
            margin-bottom: 10px;
            padding-right: 10px;
        }

        .section-content li::marker {
            color: #3498db;
            font-size: 1.2em;
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
    </style>
""", unsafe_allow_html=True)


# --- UNIFIED AUTHENTICATION BLOCK ---
creds = auth_manager.authenticate()
user_id = st.session_state.get('user_id')

if not creds or not user_id:
    st.error("مصادقة المستخدم مطلوبة. يرجى العودة إلى الصفحة الرئيسية وتسجيل الدخول.")
    st.stop()
# -----------------------------------------

# --- Helper function to render a styled section ---
def render_section(icon, title, content_html):
    st.markdown(f"""
    <div class="section-card">
        <div class="section-header">
            <span class="icon">{icon}</span>
            <h2>{title}</h2>
        </div>
        <div class="section-content">
            {content_html}
        </div>
    </div>
    """, unsafe_allow_html=True)


# --- Page Title ---
st.title("❓ عن تطبيق ماراثون القراءة")
st.markdown("<p style='font-size: 1.2em; text-align: center; color: #5D6D7E;'>أهلاً بك في الدليل الشامل! هنا، ستجد كل ما تحتاج لمعرفته حول كيفية عمل التطبيق، من فلسفة النقاط إلى شرح الألقاب والأخبار.</p>", unsafe_allow_html=True)
st.divider()


# --- Section 1: Philosophy of Points ---
philosophy_html = """
    <p>
    هذا هو قلب المشروع النابض، وهو مصمم لتحقيق توازن دقيق بين القراءة الجماعية المنظمة والقراءة الفردية الحرة، لخلق جو حماسي ومرن.
    </p>
    <h4>حرية الاختيار هي الأساس</h4>
    <p>لا يوجد مسار إلزامي. العضو لديه الحرية الكاملة ليختار المسار الذي يناسبه:</p>
    <ul>
        <li><b>مسار الكتاب المشترك:</b> يقرأ الكتاب الذي تم اختياره للتحدي. إنهاؤه يمنحه <strong>دفعة هائلة من النقاط</strong> تقديرًا لالتزامه وتهيئته لجلسة النقاش.</li>
        <li><b>مسار الكتاب الحر:</b> يقرأ أي كتاب آخر من اختياره. هنا، تتضاعف نقاطه بناءً على <strong>وقت القراءة</strong>، لكن نقاط إنهاء الكتاب تكون أقل.</li>
    </ul>
    <h4>منطق النقاط الذكي للموازنة</h4>
    <ul>
        <li><b>للتشجيع على الالتزام:</b> نقاط إنهاء الكتاب المشترك <strong>أعلى بكثير</strong>.</li>
        <li><b>لتعزيز المشاركة المجتمعية:</b> حضور جلسة النقاش الخاصة بالكتاب المشترك يمنح نقاطًا إضافية.</li>
        <li><b>لتشجيع القراءة العميقة:</b> إضافة <strong>اقتباس</strong> من كتاب يقرأه العضو يمنحه نقاطًا إضافية.</li>
    </ul>
"""
render_section("🎯", "نظام المسابقات والنقاط: فلسفة التحفيز الذكي", philosophy_html)


# --- Section 2: Hall of Fame Explained ---
st.markdown(
    """
    <div class="section-card">
        <div class="section-header">
            <span class="icon">🌟</span>
            <h2>فك شفرة الأبطال: شرح لوحة الشرف</h2>
        </div>
        <div class="section-content">
            <p>لوحة شرف الأبطال هي احتفاء بالإنجازات المتميزة في الماراثون. إليك معنى كل لقب:</p>
        </div>
    </div>
    """, unsafe_allow_html=True
)
col1, col2 = st.columns(2)
with col1:
    st.markdown("""
    <div class="section-content" style="padding: 0 20px 20px 20px;">
        <ul>
            <li><b>🧠 العقل المدبّر:</b> يُمنح للعضو الذي جمع <strong>أعلى عدد من النقاط</strong>.</li>
            <li><b>⏳ سيد الساعات:</b> يُمنح للعضو الذي سجل <strong>أطول وقت قراءة إجمالي</strong>.</li>
            <li><b>📚 الديدان القارئ:</b> يُمنح للعضو الذي <strong>أنهى أكبر عدد من الكتب</strong>.</li>
            <li><b>💎 صائد الدرر:</b> يُمنح للعضو الذي أرسل <strong>أكبر عدد من الاقتباسات</strong>.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown("""
    <div class="section-content" style="padding: 0 20px 20px 20px;">
        <ul>
            <li><b>🏃‍♂️ صاحب النَفَس الطويل:</b> يُمنح للعضو الذي سجل القراءة في <strong>أكبر عدد من الأيام</strong>.</li>
            <li><b>⚡ العدّاء السريع:</b> يُمنح للعضو الذي سجل <strong>أعلى قراءة في يوم واحد</strong>.</li>
            <li><b>⭐ نجم الأسبوع:</b> يُمنح للعضو الذي سجل <strong>أعلى قراءة خلال أسبوع واحد</strong>.</li>
            <li><b>💪 عملاق الشهر:</b> يُمنح للعضو الذي سجل <strong>أعلى قراءة خلال شهر واحد</strong>.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)


# --- Section 3: News Ticker Explained ---
news_html = """
    <p>شريط الأخبار هو نافذتك على أحدث المستجدات في الماراثون، ويعمل بطريقتين مختلفتين حسب الصفحة:</p>
    <h4>في لوحة التحكم العامة</h4>
    <ul>
        <li>يعرض الشريط هنا <strong>التغييرات التي طرأت على لوحة شرف الأبطال خلال آخر 7 أيام</strong>.</li>
        <li>الهدف هو تسليط الضوء على الديناميكية والمنافسة على مستوى الماراثون ككل.</li>
    </ul>
    <h4>في صفحة تحليلات التحديات</h4>
    <ul>
        <li>يركز الشريط هنا على <strong>أحداث التحدي المحدد فقط</strong>.</li>
        <li>يعرض الأخبار بتسلسل زمني، مع التركيز على آخر المستجدات (مثل من أنهى الكتاب ومتى).</li>
    </ul>
"""
render_section("📰", "نشرة الماراثون: كيف تعمل \"آخر الأخبار\"؟", news_html)


# --- Section 4: Q&A ---
qa_html = """
    <h4>كيف يتم حساب النقاط بالضبط؟</h4>
    <p>يتم حساب النقاط بناءً على نظام النقاط الافتراضي الذي يمكنك تعديله. يمكنك مراجعة نظام النقاط الحالي من صفحة "الإدارة والإعدادات".</p>
    <h4>هل يمكنني تعديل نظام النقاط؟</h4>
    <p>نعم! كمدير للماراثون، يمكنك الذهاب إلى صفحة "الإدارة والإعدادات" وتعديل نظام النقاط الافتراضي، أو تعيين نظام نقاط خاص لكل تحدي على حدة.</p>
    <h4>ماذا لو نسيت تسجيل قراءتي ليوم ما؟</h4>
    <p>لا تقلق. يمكن لمدير الماراثون الذهاب إلى "الإدارة والإعدادات" ثم "محرر السجلات" لتعديل أي سجل سابق لأي عضو. بعد الحفظ، يجب إعادة مزامنة البيانات.</p>
"""
render_section("🤔", "أسئلة شائعة", qa_html)


# --- Section 5: About the Developer ---
developer_html = """
    <div class="contact-links">
        <p><strong>الاسم:</strong> احمد نايفه</p>
        <p><strong>الهدف من المشروع:</strong> يهدف هذا المشروع إلى توفير أداة عصرية ومحفزة للمجموعات القرائية في الوطن العربي، للمساهمة في تعزيز ثقافة القراءة وجعلها تجربة تفاعلية وممتعة.</p>
        <h4><strong>للتواصل والدعم الفني</strong></h4>
        <ul>
            <li><strong>البريد الإلكتروني:</strong> <a href="mailto:ahmadnayfeh2000@gmail.com">ahmadnayfeh2000@gmail.com</a></li>
            <li><strong>Portfolio:</strong> <a href="https://ahmadnayfeh.vercel.app/" target="_blank">ahmadnayfeh.vercel.app</a></li>
            <li><strong>LinkedIn:</strong> <a href="https://www.linkedin.com/in/ahmad-nayfeh2000/" target="_blank">in/ahmad-nayfeh2000</a></li>
            <li><strong>GitHub:</strong> <a href="https://github.com/Ahmad-Nayfeh" target="_blank">Ahmad-Nayfeh</a></li>
        </ul>
    </div>
"""
render_section("🧑‍💻", "عن المطور", developer_html)
