import streamlit as st
import db_manager as db
import auth_manager

import style_manager  # <-- السطر الأول

style_manager.apply_sidebar_styles()  # <-- السطر الثاني

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

        /* --- Custom Expander Styles (Enhanced Design) --- */
        div[data-testid="stExpander"] {
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            border: 1px solid #e3e6ea;
            border-radius: 16px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.06);
            margin: 12px 0;
            transition: all 0.3s ease;
            overflow: hidden;
            position: relative;
        }

        div[data-testid="stExpander"]:hover {
            box-shadow: 0 12px 35px rgba(0, 0, 0, 0.1);
            transform: translateY(-2px);
        }

        /* Elegant gradient accent line */
        div[data-testid="stExpander"]::before {
            content: '';
            position: absolute;
            top: 0;
            right: 0;
            left: 0;
            height: 4px;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            border-radius: 16px 16px 0 0;
        }

        /* Style for the expander header */
        div[data-testid="stExpander"] summary {
            font-size: 1.4em !important;
            font-weight: 700;
            color: #2c3e50;
            padding: 20px 25px;
            background: rgba(255, 255, 255, 0.8);
            border-radius: 0 0 12px 12px;
            margin-bottom: 5px;
            position: relative;
        }

        /* Subtle icon enhancement */
        div[data-testid="stExpander"] summary::before {
            content: '';
            position: absolute;
            right: 25px;
            top: 50%;
            transform: translateY(-50%);
            width: 6px;
            height: 6px;
            background: #667eea;
            border-radius: 50%;
            box-shadow: 0 0 0 8px rgba(102, 126, 234, 0.1);
        }
        
        /* Style for the expander content area */
        div[data-testid="stExpander"] [data-testid="stExpanderDetails"] {
            padding: 5px 30px 25px 30px;
            background: rgba(255, 255, 255, 0.95);
        }

        /* --- Enhanced Content Styles --- */
        .section-content h4 {
            color: #1a5276;
            font-size: 1.2em;
            font-weight: 600;
            margin-top: 25px;
            margin-bottom: 12px;
            position: relative;
            padding-right: 15px;
        }

        .section-content h4::before {
            content: '';
            position: absolute;
            right: 0;
            top: 50%;
            transform: translateY(-50%);
            width: 4px;
            height: 20px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 2px;
        }
        
        .section-content p, .section-content li {
            font-size: 1.05em !important;
            line-height: 1.8 !important;
            color: #34495e;
            font-weight: 400;
        }
        
        .section-content ul {
            list-style: none;
            padding-right: 0;
            margin-bottom: 20px;
        }
        
        .section-content li {
            margin-bottom: 12px;
            padding-right: 25px;
            position: relative;
            transition: all 0.2s ease;
        }

        .section-content li:hover {
            color: #2c3e50;
            transform: translateX(-3px);
        }

        .section-content li::before {
            content: '';
            position: absolute;
            right: 0;
            top: 12px;
            width: 8px;
            height: 8px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 50%;
            box-shadow: 0 2px 4px rgba(102, 126, 234, 0.3);
        }
        
        .section-content b, .section-content strong {
            color: #1a5276;
            font-weight: 600;
        }
        
        .contact-links a {
            text-decoration: none;
            color: #667eea;
            font-weight: 500;
            transition: all 0.3s ease;
            padding: 2px 8px;
            border-radius: 6px;
        }
        .contact-links a:hover {
            background: rgba(102, 126, 234, 0.1);
            color: #4c63d2;
            transform: translateX(-2px);
        }

        /* Enhanced intro text */
        .intro-text {
            font-size: 1.15em;
            color: #5D6D7E;
            text-align: center;
            padding: 20px;
            background: rgba(255, 255, 255, 0.8);
            border-radius: 12px;
            margin: 20px 0;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        }

        /* Custom divider */
        .custom-divider {
            height: 2px;
            background: linear-gradient(90deg, transparent, #667eea, transparent);
            margin: 30px 0;
            border-radius: 2px;
        }

        /* Enhanced title styling */
        .main-title {
            text-align: center;
            color: #2c3e50;
            font-weight: 700;
            margin-bottom: 10px;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
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
st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)


# --- Section 1: الفكرة والجمهور المستهدف ---
with st.expander("🎯 الفكرة والجمهور المستهدف"):
    st.markdown("""
    <div class="section-content">
        <p>هذا التطبيق مصمم خصيصاً لمشرفي المجموعات القرائية. أنت، كمشرف، الشخص الوحيد الذي يحتاج إلى استخدام هذه المنصة. أما أعضاء فريقك، فكل ما عليهم فعله هو استخدام رابط نموذج جوجل الذي ستوفره لهم لتسجيل قراءاتهم اليومية.</p>
        <p><strong>ببساطة:</strong> أنت تدير وتحلل هنا، وهم يسجلون هناك. الهدف هو منحك القوة التحليلية الكاملة بأقل مجهود ممكن من الأعضاء.</p>
    </div>
    """, unsafe_allow_html=True)


# --- Section 2: آلية عمل التطبيق ---
with st.expander("⚙️ آلية عمل التطبيق: من الإعداد إلى المزامنة"):
    st.markdown("""
    <div class="section-content">
        <p>يعتمد التطبيق على الربط الآمن مع حسابك في جوجل لتسهيل كل شيء. عند إعداد حسابك لأول مرة، يقوم التطبيق تلقائياً بإنشاء جدول بيانات وبرنامج تسجيل خاصين بك ومملوكين لك بالكامل.</p>
        
        <h4>نموذج التسجيل</h4>
        <p>هو الأداة البسيطة والمباشرة التي يستخدمها أعضاء فريقك لتسجيل قراءاتهم اليومية في أي وقت ومن أي جهاز.</p>
        
        <h4>جدول البيانات</h4>
        <p>هو قاعدة البيانات التي يتم فيها تخزين جميع الردود والسجلات بشكل آمن ومنظم في حسابك الخاص على جوجل درايف.</p>
        
        <h4>المزامنة والتحديث</h4>
        <p>لست بحاجة للدخول إلى التطبيق يومياً. متى ما أردت الاطلاع على آخر النتائج والتحليلات، كل ما عليك فعله هو الضغط على زر "🔄 تحديث وسحب البيانات" الموجود في الشريط الجانبي، وسيقوم التطبيق بسحب آخر البيانات من ملفك، معالجتها، وتحديث جميع الإحصائيات والرسوم البيانية في ثوانٍ.</p>
    </div>
    """, unsafe_allow_html=True)


# --- Section 3: إدارة المشاركين ---
with st.expander("👥 إدارة المشاركين: إضافة وتعطيل"):
    st.markdown("""
    <div class="section-content">
        <h4>إضافة أعضاء جدد</h4>
        <p>يمكنك بسهولة إضافة أعضاء جدد في أي وقت. سيقوم التطبيق تلقائياً بتحديث قائمة الأسماء في نموذج التسجيل ليشملهم فوراً.</p>
        
        <h4>تعطيل الأعضاء</h4>
        <p>إذا قرر أحد الأعضاء أخذ استراحة أو مغادرة المجموعة، يمكنك "تعطيله" بدلاً من حذفه. هذه الميزة تحافظ على بياناته وإنجازاته السابقة في سجلاتك، وتمنعه من الظهور في قوائم المتصدرين الحالية. يمكنك إعادة تفعيله بسهولة في أي وقت ليعود للمنافسة.</p>
    </div>
    """, unsafe_allow_html=True)


# --- Section 4: إدارة التحديات ---
with st.expander("📖 إدارة التحديات: إضافة وحذف"):
    st.markdown("""
    <div class="section-content">
        <h4>إضافة تحدي جديد</h4>
        <p>يمكنك التخطيط للمستقبل وإضافة تحديات قادمة بكتب جديدة. لديك خياران عند إضافة تحدي:</p>
        <ul>
            <li><strong>استخدام نظام النقاط الافتراضي:</strong> لتطبيق القواعد العامة التي قمت بضبطها مسبقاً للماراثون.</li>
            <li><strong>استخدام نظام نقاط مخصوص:</strong> لوضع قواعد خاصة ومختلفة لهذا التحدي فقط (مثلاً، تحدي سريع في إجازة نهاية الأسبوع بقواعد مختلفة).</li>
        </ul>
        
        <h4>حذف تحدي</h4>
        <p>يمكنك حذف التحديات (المنتهية أو المقبلة) إذا لزم الأمر. سيقوم التطبيق بحذف التحدي وجميع الإنجازات المتعلقة به بشكل نهائي.</p>
    </div>
    """, unsafe_allow_html=True)


# --- Section 5: فلسفة التحفيز الذكي ---
with st.expander("🧠 فلسفة التحفيز الذكي: وسائل كسب النقاط"):
    st.markdown("""
    <div class="section-content">
        <p>تم تصميم نظام النقاط بعناية فائقة لمعالجة التحديات الجوهرية التي تواجه المجموعات القرائية، وتحقيق توازن دقيق بين الالتزام الجماعي والحرية الفردية، مما يضمن بقاء التجربة ممتعة ومحفزة للجميع.</p>
        
        <h4>حل لمشكلة "الكتاب الإجباري"</h4>
        <p>تواجه الكثير من المجموعات معضلة: إما أن تتفكك بسبب عدم وجود كتاب مشترك يجمعها، أو تتحول إلى تجربة "ديكتاتورية" تجبر الجميع على قراءة كتاب قد لا يروق لهم. هذا التطبيق يقدم حلاً متوازناً:</p>
        <ul>
            <li>يتيح النظام للقارئ حرية الاختيار بين قراءة الكتاب المشترك أو قراءة أي كتاب آخر من اهتماماته الشخصية، أو حتى كليهما معاً.</li>
            <li><strong>التحفيز على الالتزام:</strong> يتم منح دفعة نقاط أعلى بكثير عند "إنهاء الكتاب المشترك".</li>
            <li><strong>مكافحة الانقطاع:</strong> يتم منح نقاط أعلى على "وقت القراءة" للكتب الأخرى.</li>
        </ul>
        
        <h4>تحفيز التفاعل عبر "الاقتباسات"</h4>
        <p>إرسال اقتباس من كتاب يمنح نقاطاً إضافية. هذه الميزة البسيطة تحول مجموعة التواصل من مجموعة صامتة إلى مساحة تفاعلية وحيوية لتبادل الأفكار والفوائد.</p>
        
        <h4>تتويج التجربة بـ "جلسة النقاش"</h4>
        <p>حضور جلسة النقاش في نهاية كل تحدي يمنح دفعة كبيرة من النقاط. هذه الجلسة هي الرابط الاجتماعي الذي يقرب بين الأعضاء ويحول التجربة من مجرد قراءة صامتة إلى حوار فكري مثمر.</p>
        
        <h4>الهدف الأسمى من النقاط</h4>
        <p>الفائز في كل تحدي (صاحب أعلى نقاط) يحصل على شرف اختيار الكتاب المشترك للتحدي القادم! هذا يضيف بعداً استراتيجياً وممتعاً للمنافسة.</p>
    </div>
    """, unsafe_allow_html=True)


# --- Section 6: نظام النقاط والأوسمة ---
with st.expander("🏆 نظام النقاط والأوسمة"):
    st.markdown("""
    <div class="section-content">
        <h4>نظام النقاط الافتراضي والمخصوص</h4>
        <p>يمكنك كمشرف تعديل نظام النقاط الافتراضي الذي سيتم تطبيقه على كل التحديات الجديدة من صفحة "الإدارة والإعدادات". هذا يمنحك المرونة لتكييف التجربة مع طبيعة مجموعتك. كما يمكنك وضع نظام نقاط مختلف تماماً لتحدي معين عند إنشائه.</p>
        
        <h4>الأوسمة والشارات</h4>
        <p>بالإضافة إلى النقاط، هناك نظام أوسمة يكافئ الإنجازات الخاصة التي لا تظهر في لوحة الصدارة بالضرورة، مثل "وسام المثابرة" للقراءة لأيام متتالية، أو "وسام العدّاء" لإنهاء كتاب في الأسبوع الأول، مما يضيف طبقة أخرى من التحفيز والتقدير لجميع أنواع القراء.</p>
    </div>
    """, unsafe_allow_html=True)


# --- Section 7: أدوات التحليل والمتابعة ---
with st.expander("📊 أدوات التحليل والمتابعة: شرح لوحات التحكم"):
    st.markdown("""
    <div class="section-content">
        <h4>لوحة التحكم العامة</h4>
        <ul>
            <li><strong>مؤشرات الأداء الرئيسية:</strong> تعطيك نظرة سريعة وشاملة على أرقام الماراثون الكلية (إجمالي ساعات القراءة، عدد الكتب المنهاة، إلخ) لتقييم صحة ونشاط المجموعة بشكل عام.</li>
            <li><strong>لوحة شرف الأبطال:</strong> تحتفي بالمتصدرين في فئات متنوعة مثل "العقل المدبّر" (الأعلى نقاطاً) و"سيد الساعات" (الأطول وقتاً في القراءة).</li>
        </ul>
        
        <h4>تحليلات التحديات</h4>
        <ul>
            <li><strong>ملخص التحدي:</strong> يعرض لوحة مؤشرات ورسومات بيانية خاصة بالتحدي المحدد فقط.</li>
            <li><strong>بطاقة القارئ:</strong> تعرض ملفاً تفصيلياً لكل قارئ، مع إحصائياته الإجمالية، والأوسمة التي حصل عليها، ومصادر نقاطه.</li>
        </ul>
        
        <h4>شريط "آخر الأخبار"</h4>
        <ul>
            <li><strong>في لوحة التحكم العامة:</strong> يعرض التغييرات التي طرأت على "لوحة شرف الأبطال" خلال آخر 7 أيام.</li>
            <li><strong>في صفحة تحليلات التحديات:</strong> يركز فقط على أحداث التحدي المحدد، مثل من أنهى الكتاب ومتى.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)


# --- Section 8: أدوات إدارية متقدمة ---
with st.expander("⚙️ أدوات إدارية متقدمة: محرر السجلات وتصدير التقارير"):
    st.markdown("""
    <div class="section-content">
        <h4>محرر السجلات الذكي</h4>
        <p>هل نسي أحد الأعضاء تسجيل قراءته ليوم ما أو أخطأ في إدخال البيانات؟ لا مشكلة. تتيح لك هذه الأداة القوية تعديل أي سجل قراءة سابق مباشرة من التطبيق، مما يضمن دقة البيانات وصحة النتائج.</p>
        
        <h4>تصدير تقارير PDF</h4>
        <p>يمكنك بنقرة زر إنشاء تقارير PDF احترافية وقابلة للمشاركة لـ:</p>
        <ul>
            <li><strong>لوحة التحكم العامة:</strong> لملخص شامل للماراثون يمكن مشاركته في نهاية كل عام أو فترة.</li>
            <li><strong>ملخص التحدي:</strong> لتقرير مفصل عن أداء تحدي معين يمكن مشاركته بعد انتهاء التحدي.</li>
            <li><strong>بطاقة القارئ:</strong> لتقرير شخصي بإنجازات وأداء كل عضو، يمكن إرساله له كشهادة تقدير.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)


# --- Section 9: عن المطور ---
with st.expander("🧑‍💻 عن المطور"):
    st.markdown("""
    <div class="section-content contact-links">
        <p><strong>الاسم:</strong> احمد نايفه</p>
        <p><strong>الهدف من المشروع:</strong> توفير أداة عصرية ومحفزة للمجموعات القرائية في الوطن العربي، لتعزيز ثقافة القراءة وجعلها تجربة تفاعلية وممتعة.</p>
        <h4>للتواصل والدعم الفني</h4>
        <ul>
            <li><strong>البريد الإلكتروني:</strong> <a href="mailto:ahmadnayfeh2000@gmail.com">ahmadnayfeh2000@gmail.com</a></li>
            <li><strong>Portfolio:</strong> <a href="https://ahmadnayfeh.vercel.app/" target="_blank">ahmadnayfeh.vercel.app</a></li>
            <li><strong>LinkedIn:</strong> <a href="https://www.linkedin.com/in/ahmad-nayfeh2000/" target="_blank">in/ahmad-nayfeh2000</a></li>
        </ul>
    </div>
    """, unsafe_allow_html=True)