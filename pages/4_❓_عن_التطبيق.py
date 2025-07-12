import streamlit as st
import db_manager as db
import auth_manager

import style_manager

style_manager.apply_sidebar_styles()

st.set_page_config(
    page_title="عن التطبيق",
    page_icon="❓",
    layout="wide"
)

# --- ADVANCED STYLING (CSS) ---
# This new style block addresses font hierarchy and adds modern aesthetics.
st.markdown("""
    <style>
        /* --- Base & Background --- */
        .stApp {
            direction: rtl;
            background-color: #f0f2f6; /* Light gray background to lift elements */
        }
        [data-testid="stSidebar"] {
            direction: rtl;
        }

        /* --- Typography Hierarchy --- */
        h1, h2, h3, h4, h5, h6, p, li, .st-write, div[data-testid="stMarkdownContainer"] {
            text-align: right !important;
            font-family: 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
        }

        /* --- Main Title (Gradient Text) --- */
        .main-title {
            text-align: center;
            font-weight: 700;
            margin-bottom: 25px;
            font-size: 3em; /* Larger main title */
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-fill-color: transparent;
        }
        
        /* --- Intro Text --- */
        .intro-text {
            font-size: 1.15em;
            color: #5D6D7E;
            text-align: center;
            padding: 20px;
            background-color: #ffffff;
            border-radius: 12px;
            margin: 20px auto;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            max-width: 80%;
        }

        /* --- Modern Expander (Card) Design --- */
        div[data-testid="stExpander"] {
            border: none;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            margin: 20px 0 !important;
            overflow: hidden;
            background-color: #ffffff;
            transition: box-shadow 0.3s ease-in-out;
        }
        div[data-testid="stExpander"]:hover {
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
            transform: translateY(-2px);
        }

        /* --- Expander Header (Card Title) --- */
        div[data-testid="stExpander"] summary {
            font-size: 1.5em !important;  /* Bigger & Bolder Card Title */
            font-weight: 600;
            color: #2D3748;
            padding: 20px 25px;
            background-color: #fcfcfc;
            border-bottom: 1px solid #e2e8f0;
        }

        /* --- Expander Content Area --- */
        div[data-testid="stExpanderDetails"] {
            padding: 15px 25px 25px 25px;
        }
        
        /* --- Content: Subheaders (h3 from st.subheader) --- */
        div[data-testid="stExpanderDetails"] h3 {
            font-size: 1.25em; /* Clearly a sub-heading */
            font-weight: 600;
            color: #764ba2; /* Accent color */
            border-bottom: 2px solid #e3e6ea;
            padding-bottom: 8px;
            margin-top: 15px;
            margin-bottom: 15px;
        }
        
        /* --- Content: Paragraphs (p from st.write) --- */
        div[data-testid="stExpanderDetails"] p {
            font-size: 1.05em !important; /* Readable content size */
            line-height: 1.8 !important;
            color: #4A5568; /* Softer than pure black */
        }

        /* --- Content: Lists (from st.markdown) --- */
        div[data-testid="stExpanderDetails"] ul {
             padding-right: 20px;
        }
        div[data-testid="stExpanderDetails"] li {
            margin-bottom: 12px;
            line-height: 1.7;
            font-size: 1.05em;
            color: #4A5568;
        }
        div[data-testid="stExpanderDetails"] li strong {
            color: #667eea; /* Accent color for bolded text in lists */
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
st.markdown('<h1 class="main-title">❓ عن تطبيق ماراثون القراءة</h1>', unsafe_allow_html=True)
st.markdown('<div class="intro-text">أهلاً بك في الدليل الشامل لتطبيق "ماراثون القراءة"! هذه المنصة صُممت لتكون أداتك المركزية لإدارة سباقات القراءة الجماعية، وتحويلها من مجرد هواية إلى تجربة تفاعلية، محفزة، وذات أثر عميق.</div>', unsafe_allow_html=True)


# --- Section 1: الفكرة والجمهور المستهدف ---
with st.expander("🎯 الفكرة والجمهور المستهدف"):
    st.write("هذا التطبيق مصمم خصيصاً لمشرفي المجموعات القرائية. أنت، كمشرف، الشخص الوحيد الذي يحتاج إلى استخدام هذه المنصة. أما أعضاء فريقك، فكل ما عليهم فعله هو استخدام رابط نموذج جوجل الذي ستوفره لهم لتسجيل قراءاتهم اليومية.")
    st.write("**ببساطة:** أنت تدير وتحلل هنا، وهم يسجلون هناك. الهدف هو منحك القوة التحليلية الكاملة بأقل مجهود ممكن من الأعضاء.")

# --- Section 2: آلية عمل التطبيق ---
with st.expander("⚙️ آلية عمل التطبيق: من الإعداد إلى المزامنة"):
    st.write("يعتمد التطبيق على الربط الآمن مع حسابك في جوجل لتسهيل كل شيء. عند إعداد حسابك لأول مرة، يقوم التطبيق تلقائياً بإنشاء جدول بيانات وبرنامج تسجيل خاصين بك ومملوكين لك بالكامل.")
    st.subheader("نموذج التسجيل")
    st.write("هو الأداة البسيطة والمباشرة التي يستخدمها أعضاء فريقك لتسجيل قراءاتهم اليومية في أي وقت ومن أي جهاز.")
    st.subheader("جدول البيانات")
    st.write("هو قاعدة البيانات التي يتم فيها تخزين جميع الردود والسجلات بشكل آمن ومنظم في حسابك الخاص على جوجل درايف.")
    st.subheader("المزامنة والتحديث")
    st.write('لست بحاجة للدخول إلى التطبيق يومياً. متى ما أردت الاطلاع على آخر النتائج والتحليلات، كل ما عليك فعله هو الضغط على زر "🔄 تحديث وسحب البيانات" الموجود في الشريط الجانبي، وسيقوم التطبيق بسحب آخر البيانات من ملفك، معالجتها، وتحديث جميع الإحصائيات والرسوم البيانية في ثوانٍ.')

# --- Section 3: إدارة المشاركين ---
with st.expander("👥 إدارة المشاركين: إضافة وتعطيل"):
    st.subheader("إضافة أعضاء جدد")
    st.write("يمكنك بسهولة إضافة أعضاء جدد في أي وقت. سيقوم التطبيق تلقائياً بتحديث قائمة الأسماء في نموذج التسجيل ليشملهم فوراً.")
    st.subheader("تعطيل الأعضاء")
    st.write('إذا قرر أحد الأعضاء أخذ استراحة أو مغادرة المجموعة، يمكنك "تعطيله" بدلاً من حذفه. هذه الميزة تحافظ على بياناته وإنجازاته السابقة في سجلاتك، وتمنعه من الظهور في قوائم المتصدرين الحالية. يمكنك إعادة تفعيله بسهولة في أي وقت ليعود للمنافسة.')

# --- Section 4: إدارة التحديات ---
with st.expander("📖 إدارة التحديات: إضافة وحذف"):
    st.subheader("إضافة تحدي جديد")
    st.write("يمكنك التخطيط للمستقبل وإضافة تحديات قادمة بكتب جديدة. لديك خياران عند إضافة تحدي:")
    st.markdown("""
    - **استخدام نظام النقاط الافتراضي:** لتطبيق القواعد العامة التي قمت بضبطها مسبقاً للماراثون.
    - **استخدام نظام نقاط مخصوص:** لوضع قواعد خاصة ومختلفة لهذا التحدي فقط (مثلاً، تحدي سريع في إجازة نهاية الأسبوع بقواعد مختلفة).
    """)
    st.subheader("حذف تحدي")
    st.write("يمكنك حذف التحديات (المنتهية أو المقبلة) إذا لزم الأمر. سيقوم التطبيق بحذف التحدي وجميع الإنجازات المتعلقة به بشكل نهائي.")

# --- Section 5: فلسفة التحفيز الذكي ---
with st.expander("🧠 فلسفة التحفيز الذكي: وسائل كسب النقاط"):
    st.write("تم تصميم نظام النقاط بعناية فائقة لمعالجة التحديات الجوهرية التي تواجه المجموعات القرائية، وتحقيق توازن دقيق بين الالتزام الجماعي والحرية الفردية، مما يضمن بقاء التجربة ممتعة ومحفزة للجميع.")
    st.subheader('حل لمشكلة "الكتاب الإجباري"')
    st.write('تواجه الكثير من المجموعات معضلة: إما أن تتفكك بسبب عدم وجود كتاب مشترك يجمعها، أو تتحول إلى تجربة "ديكتاتورية" تجبر الجميع على قراءة كتاب قد لا يروق لهم. هذا التطبيق يقدم حلاً متوازناً:')
    st.markdown("""
    - يتيح النظام للقارئ حرية الاختيار بين قراءة الكتاب المشترك أو قراءة أي كتاب آخر من اهتماماته الشخصية، أو حتى كليهما معاً.
    - **التحفيز على الالتزام:** يتم منح دفعة نقاط أعلى بكثير عند "إنهاء الكتاب المشترك".
    - **مكافحة الانقطاع:** يتم منح نقاط أعلى على "وقت القراءة" للكتب الأخرى.
    """)
    st.subheader('تحفيز التفاعل عبر "الاقتباسات"')
    st.write("إرسال اقتباس من كتاب يمنح نقاطاً إضافية. هذه الميزة البسيطة تحول مجموعة التواصل من مجموعة صامتة إلى مساحة تفاعلية وحيوية لتبادل الأفكار والفوائد.")
    st.subheader('تتويج التجربة بـ "جلسة النقاش"')
    st.write("حضور جلسة النقاش في نهاية كل تحدي يمنح دفعة كبيرة من النقاط. هذه الجلسة هي الرابط الاجتماعي الذي يقرب بين الأعضاء ويحول التجربة من مجرد قراءة صامتة إلى حوار فكري مثمر.")
    st.subheader("الهدف الأسمى من النقاط")
    st.write("الفائز في كل تحدي (صاحب أعلى نقاط) يحصل على شرف اختيار الكتاب المشترك للتحدي القادم! هذا يضيف بعداً استراتيجياً وممتعاً للمنافسة.")

# --- Section 6: نظام النقاط والأوسمة ---
with st.expander("🏆 نظام النقاط والأوسمة"):
    st.subheader("نظام النقاط الافتراضي والمخصوص")
    st.write("يمكنك كمشرف تعديل نظام النقاط الافتراضي الذي سيتم تطبيقه على كل التحديات الجديدة من صفحة \"الإدارة والإعدادات\". هذا يمنحك المرونة لتكييف التجربة مع طبيعة مجموعتك. كما يمكنك وضع نظام نقاط مختلف تماماً لتحدي معين عند إنشائه.")
    st.subheader("الأوسمة والشارات")
    st.write("بالإضافة إلى النقاط، هناك نظام أوسمة يكافئ الإنجازات الخاصة التي لا تظهر في لوحة الصدارة بالضرورة، مثل \"وسام المثابرة\" للقراءة لأيام متتالية، أو \"وسام العدّاء\" لإنهاء كتاب في الأسبوع الأول، مما يضيف طبقة أخرى من التحفيز والتقدير لجميع أنواع القراء.")

# --- Section 7: أدوات التحليل والمتابعة ---
with st.expander("📊 أدوات التحليل والمتابعة: شرح لوحات التحكم"):
    st.subheader("لوحة التحكم العامة")
    st.markdown("""
    - **مؤشرات الأداء الرئيسية:** تعطيك نظرة سريعة وشاملة على أرقام الماراثون الكلية (إجمالي ساعات القراءة، عدد الكتب المنهاة، إلخ) لتقييم صحة ونشاط المجموعة بشكل عام.
    - **لوحة شرف الأبطال:** تحتفي بالمتصدرين في فئات متنوعة مثل "العقل المدبّر" (الأعلى نقاطاً) و"سيد الساعات" (الأطول وقتاً في القراءة).
    """)
    st.subheader("تحليلات التحديات")
    st.markdown("""
    - **ملخص التحدي:** يعرض لوحة مؤشرات ورسومات بيانية خاصة بالتحدي المحدد فقط.
    - **بطاقة القارئ:** تعرض ملفاً تفصيلياً لكل قارئ، مع إحصائياته الإجمالية، والأوسمة التي حصل عليها، ومصادر نقاطه.
    """)
    st.subheader('شريط "آخر الأخبار"')
    st.markdown("""
    - **في لوحة التحكم العامة:** يعرض التغييرات التي طرأت على "لوحة شرف الأبطال" خلال آخر 7 أيام.
    - **في صفحة تحليلات التحديات:** يركز فقط على أحداث التحدي المحدد، مثل من أنهى الكتاب ومتى.
    """)

# --- Section 8: أدوات إدارية متقدمة ---
with st.expander("⚙️ أدوات إدارية متقدمة: محرر السجلات وتصدير التقارير"):
    st.subheader("محرر السجلات الذكي")
    st.write("هل نسي أحد الأعضاء تسجيل قراءته ليوم ما أو أخطأ في إدخال البيانات؟ لا مشكلة. تتيح لك هذه الأداة القوية تعديل أي سجل قراءة سابق مباشرة من التطبيق، مما يضمن دقة البيانات وصحة النتائج.")
    st.subheader("تصدير تقارير PDF")
    st.write("يمكنك بنقرة زر إنشاء تقارير PDF احترافية وقابلة للمشاركة لـ:")
    st.markdown("""
    - **لوحة التحكم العامة:** لملخص شامل للماراثون يمكن مشاركته في نهاية كل عام أو فترة.
    - **ملخص التحدي:** لتقرير مفصل عن أداء تحدي معين يمكن مشاركته بعد انتهاء التحدي.
    - **بطاقة القارئ:** لتقرير شخصي بإنجازات وأداء كل عضو، يمكن إرساله له كشهادة تقدير.
    """)

# --- Section 9: عن المطور ---
with st.expander("🧑‍💻 عن المطور"):
    st.write("**الاسم:** احمد نايفه")
    st.write("**الهدف من المشروع:** توفير أداة عصرية ومحفزة للمجموعات القرائية في الوطن العربي، لتعزيز ثقافة القراءة وجعلها تجربة تفاعلية وممتعة.")
    st.subheader("للتواصل والدعم الفني")
    st.markdown("""
    - **البريد الإلكتروني:** [ahmadnayfeh2000@gmail.com](mailto:ahmadnayfeh2000@gmail.com)
    - **Portfolio:** [ahmadnayfeh.vercel.app](https://ahmadnayfeh.vercel.app/)
    - **LinkedIn:** [in/ahmad-nayfeh2000](https://www.linkedin.com/in/ahmad-nayfeh2000/)
    """)