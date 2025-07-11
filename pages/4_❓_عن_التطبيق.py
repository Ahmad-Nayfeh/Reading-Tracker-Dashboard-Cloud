import streamlit as st
import db_manager as db
import auth_manager

st.set_page_config(
    page_title="عن التطبيق",
    page_icon="❓",
    layout="wide"
)

# This CSS snippet enforces RTL and adds custom styles for the page
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
        
        /* Custom styles for the expander to make it look like a section card */
        .st-expander {
            border: 1px solid #e0e0e0 !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05) !important;
            margin-bottom: 20px !important;
        }
        .st-expander header {
            font-size: 1.5em !important;
            font-weight: bold !important;
            color: #2980b9 !important;
            padding-top: 15px !important;
            padding-bottom: 15px !important;
        }
        .st-expander [data-testid="stExpanderDetails"] {
            padding: 0 20px 20px 20px !important;
        }

        /* --- NEW Custom styles for content inside expanders --- */
        .content-section {
            padding-top: 10px;
        }
        .content-section h4 {
            color: #1a5276;
            font-size: 1.3em;
            font-weight: bold;
            border-bottom: 2px solid #aed6f1;
            padding-bottom: 8px;
            margin-top: 20px;
            margin-bottom: 15px;
        }
        .content-section p {
            font-size: 1.15em !important;
            line-height: 1.9 !important;
            color: #34495e;
            margin-bottom: 15px;
        }
        .content-section ul {
            list-style-position: outside;
            padding-right: 25px; /* Indentation for the list */
            margin: 0;
        }
        .content-section li {
            font-size: 1.1em !important;
            line-height: 1.9 !important;
            margin-bottom: 12px;
            padding-right: 10px;
        }
        .content-section li::marker {
            color: #2980b9;
            font-size: 1.2em;
        }
        .content-section b, .content-section strong {
            color: #2c3e50;
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


st.title("❓ عن تطبيق ماراثون القراءة")
st.markdown("---")
st.markdown("<p style='font-size: 1.2em; text-align: center;'>أهلاً بك في الدليل الشامل! هنا، ستجد كل ما تحتاج لمعرفته حول كيفية عمل التطبيق، من فلسفة النقاط إلى شرح الألقاب والأخبار.</p>", unsafe_allow_html=True)


# --- Section 1: Philosophy of Points ---
philosophy_html = """
<div class="content-section">
    <p>
    هذا هو قلب المشروع النابض، وهو مصمم لتحقيق توازن دقيق بين القراءة الجماعية المنظمة والقراءة الفردية الحرة، لخلق جو حماسي ومرن. يقوم النظام على الأفكار التالية:
    </p>

    <h4>حرية الاختيار هي الأساس</h4>
    <p>
    لا يوجد مسار إلزامي. العضو لديه الحرية الكاملة ليختار المسار الذي يناسبه:
    </p>
    <ul>
        <li><b>مسار الكتاب المشترك:</b> يقرأ الكتاب الذي تم اختياره للتحدي. إنهاؤه يمنحه <strong>دفعة هائلة من النقاط</strong> تقديرًا لالتزامه وتهيئته لجلسة النقاش.</li>
        <li><b>مسار الكتاب الحر:</b> يقرأ أي كتاب آخر من اختياره. هنا، تتضاعف نقاطه بناءً على <strong>وقت القراءة</strong>، لكن نقاط إنهاء الكتاب تكون أقل.</li>
    </ul>
    <p>ويمكن للعضو أن يمشي بالمسارين معًا في وقت واحد، أو حتى يقرأ عدة كتب حرة! الأمر متروك له ولهمّته.</p>

    <h4>منطق النقاط الذكي للموازنة</h4>
    <ul>
        <li><b>للتشجيع على الالتزام:</b> نقاط إنهاء الكتاب المشترك <strong>أعلى بكثير</strong>.</li>
        <li><b>لتعزيز المشاركة المجتمعية:</b> حضور جلسة النقاش الخاصة بالكتاب المشترك يمنح نقاطًا إضافية.</li>
        <li><b>لتشجيع القراءة العميقة:</b> إضافة <strong>اقتباس</strong> من كتاب يقرأه العضو يمنحه نقاطًا إضافية، مما يحفزه على التفاعل مع النص بشكل أعمق.</li>
    </ul>

    <h4>دورة حياة التحديات</h4>
    <ul>
        <li><b>بداية جديدة للجميع:</b> كل ماراثون يبدأ ونقاطه صفر، مما يعطي فرصة متجددة للمنافسة.</li>
        <li><b>مكافأة الاجتهاد المستمر:</b> يتم تجميع كل النقاط في لوحة التحكم العامة لتقدير الأبطال الحقيقيين على المدى الطويل.</li>
        <li><b>جوائز وهدايا:</b> في نهاية كل تحدٍ، يمكن تقديم جوائز لأصحاب المراكز العليا، مثل أن يقوم الفائز باختيار الكتاب المشترك للماراثون القادم.</li>
    </ul>
</div>
"""
with st.expander("🎯 نظام المسابقات والنقاط: فلسفة التحفيز الذكي", expanded=True):
    st.markdown(philosophy_html, unsafe_allow_html=True)


# --- Section 2: Hall of Fame Explained ---
heroes_html = """
<div class="content-section">
    <p>لوحة شرف الأبطال هي احتفاء بالإنجازات المتميزة في الماراثون. إليك معنى كل لقب:</p>
    <ul>
        <li><b>🧠 العقل المدبّر:</b> يُمنح للعضو الذي جمع <strong>أعلى عدد من النقاط</strong> في المجموع الكلي.</li>
        <li><b>⏳ سيد الساعات:</b> يُمنح للعضو الذي سجل <strong>أطول وقت قراءة إجمالي</strong> (مجموع قراءة الكتب المشتركة والكتب الحرة).</li>
        <li><b>📚 الديدان القارئ:</b> يُمنح للعضو الذي <strong>أنهى أكبر عدد من الكتب</strong> (مشتركة وحرة).</li>
        <li><b>💎 صائد الدرر:</b> يُمنح للعضو الذي أرسل <strong>أكبر عدد من الاقتباسات</strong>.</li>
        <li><b>🏃‍♂️ صاحب النَفَس الطويل:</b> يُمنح للعضو الأكثر ثباتًا والتزامًا، وهو من سجل القراءة في <strong>أكبر عدد من الأيام المختلفة</strong>.</li>
        <li><b>⚡ العدّاء السريع:</b> يُمنح للعضو الذي سجل <strong>أعلى عدد من دقائق القراءة في يوم واحد</strong>.</li>
        <li><b>⭐ نجم الأسبوع:</b> يُمنح للعضو الذي سجل <strong>أعلى مجموع دقائق قراءة خلال أسبوع واحد</strong>.</li>
        <li><b>💪 عملاق الشهر:</b> يُمنح للعضو الذي سجل <strong>أعلى مجموع دقائق قراءة خلال شهر واحد</strong>.</li>
    </ul>
</div>
"""
with st.expander("🌟 فك شفرة الأبطال: شرح لوحة الشرف"):
    st.markdown(heroes_html, unsafe_allow_html=True)


# --- Section 3: News Ticker Explained ---
news_html = """
<div class="content-section">
    <p>شريط الأخبار هو نافذتك على أحدث المستجدات في الماراثون، ويعمل بطريقتين مختلفتين حسب الصفحة:</p>
    
    <h4>في لوحة التحكم العامة</h4>
    <ul>
        <li>يعرض الشريط هنا <strong>التغييرات التي طرأت على لوحة شرف الأبطال خلال آخر 7 أيام</strong>.</li>
        <li>يقوم النظام بمقارنة قائمة الأبطال الحالية بقائمتهم قبل أسبوع، ويرصد أي تغييرات مثل:
            <ul>
                <li>صعود بطل جديد إلى الصدارة في أحد الألقاب.</li>
                <li>انضمام منافس جديد ومشاركته اللقب مع بطل حالي.</li>
                <li>ظهور بطل لأول مرة في لقب كان شاغرًا.</li>
            </ul>
        </li>
        <li>الهدف هو تسليط الضوء على الديناميكية والمنافسة على مستوى الماراثون ككل.</li>
    </ul>

    <h4>في صفحة تحليلات التحديات</h4>
    <ul>
        <li>يركز الشريط هنا على <strong>أحداث التحدي المحدد فقط</strong>.</li>
        <li>يعرض الأخبار بتسلسل زمني، مع التركيز على آخر المستجدات، مثل:
            <ul>
                <li>من هو أول عضو أنهى الكتاب المشترك.</li>
                <li>من هم الأعضاء الآخرون الذين أنهوا الكتاب، ومتى.</li>
                <li>بعد انتهاء التحدي، يتم عرض خبر عن الأعضاء الذين حضروا جلسة النقاش.</li>
            </ul>
        </li>
        <li>الهدف هو متابعة التقدم والإنجازات داخل كل تحدي على حدة.</li>
    </ul>
</div>
"""
with st.expander("📰 نشرة الماراثون: كيف تعمل \"آخر الأخبار\"؟"):
    st.markdown(news_html, unsafe_allow_html=True)


# --- Section 4: Q&A ---
qa_html = """
<div class="content-section">
    <h4>كيف يتم حساب النقاط بالضبط؟</h4>
    <p>
    يتم حساب النقاط بناءً على نظام النقاط الافتراضي الذي يمكنك رؤيته وتعديله. بشكل عام، تحصل على نقاط مقابل:
    </p>
    <ul>
        <li>الدقائق التي تقرؤها (للكتب المشتركة والكتب الحرة).</li>
        <li>إرسال الاقتباسات.</li>
        <li>إنهاء الكتب.</li>
        <li>حضور جلسات النقاش.</li>
    </ul>
    <p>يمكنك مراجعة نظام النقاط الحالي من صفحة "الإدارة والإعدادات".</p>

    <h4>هل يمكنني تعديل نظام النقاط؟</h4>
    <p>
    نعم! كمدير للماراثون، يمكنك الذهاب إلى صفحة "الإدارة والإعدادات" وتعديل نظام النقاط الافتراضي الذي سيطبق على التحديات الجديدة. كما يمكنك تعيين نظام نقاط خاص ومختلف لكل تحدي على حدة عند إنشائه.
    </p>

    <h4>ماذا لو نسيت تسجيل قراءتي ليوم ما؟</h4>
    <p>
    لا تقلق. يمكن لمدير الماراثون (أنت) الذهاب إلى صفحة "الإدارة والإعدادات"، ومن ثم إلى تبويب "محرر السجلات". هناك، يمكنك تعديل أي سجل سابق لأي عضو، سواء بتغيير مدة القراءة أو إضافة إنجاز تم نسيانه. بعد الحفظ، يجب إعادة مزامنة البيانات لتعكس التغييرات.
    </p>
</div>
"""
with st.expander("🤔 أسئلة شائعة"):
    st.markdown(qa_html, unsafe_allow_html=True)


# --- Section 5: About the Developer ---
developer_html = """
<div class="content-section contact-links">
    <p><strong>الاسم:</strong> احمد نايفه</p>
    <p><strong>الهدف من المشروع:</strong> يهدف هذا المشروع إلى توفير أداة عصرية ومحفزة للمجموعات القرائية في الوطن العربي، للمساهمة في تعزيز ثقافة القراءة وجعلها تجربة تفاعلية وممتعة.</p>
    
    <h4><strong>للتواصل والدعم الفني</strong></h4>
    <p>
    إذا واجهتك أي مشكلة تقنية، أو كان لديك اقتراح لتطوير التطبيق، فلا تتردد في التواصل معي عبر أحد الحسابات التالية:
    </p>
    <ul>
        <li><strong>البريد الإلكتروني:</strong> <a href="mailto:ahmadnayfeh2000@gmail.com">ahmadnayfeh2000@gmail.com</a></li>
        <li><strong>Portfolio:</strong> <a href="https://ahmadnayfeh.vercel.app/" target="_blank">ahmadnayfeh.vercel.app</a></li>
        <li><strong>LinkedIn:</strong> <a href="https://www.linkedin.com/in/ahmad-nayfeh2000/" target="_blank">in/ahmad-nayfeh2000</a></li>
        <li><strong>GitHub (للمطورين):</strong> <a href="https://github.com/Ahmad-Nayfeh" target="_blank">Ahmad-Nayfeh</a></li>
    </ul>
    <p>يسعدني دائماً تلقي ملاحظاتكم واقتراحاتكم لجعل تجربة ماراثون القراءة أفضل للجميع.</p>
</div>
"""
st.markdown("---")
with st.expander("🧑‍💻 عن المطور"):
    st.markdown(developer_html, unsafe_allow_html=True)

