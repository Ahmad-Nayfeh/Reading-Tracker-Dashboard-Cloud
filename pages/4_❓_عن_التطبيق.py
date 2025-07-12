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

# Enhanced CSS with modern design and animations
st.markdown("""
    <style>
        /* --- Import Google Fonts --- */
        @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@300;400;500;600;700;800;900&display=swap');
        
        /* --- Base RTL and Font Fixes --- */
        .stApp { 
            direction: rtl; 
            font-family: 'Tajawal', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        [data-testid="stSidebar"] { direction: rtl; }
        h1, h2, h3, h4, h5, h6, p, li { text-align: right !important; }

        /* --- Animated Background Particles --- */
        .stApp::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                radial-gradient(circle at 20% 80%, rgba(120, 119, 198, 0.3) 0%, transparent 50%),
                radial-gradient(circle at 80% 20%, rgba(255, 255, 255, 0.1) 0%, transparent 50%),
                radial-gradient(circle at 40% 40%, rgba(120, 119, 198, 0.2) 0%, transparent 50%);
            animation: float 20s ease-in-out infinite;
            pointer-events: none;
            z-index: -1;
        }

        @keyframes float {
            0%, 100% { transform: translateY(0px) rotate(0deg); }
            33% { transform: translateY(-20px) rotate(1deg); }
            66% { transform: translateY(-10px) rotate(-1deg); }
        }

        /* --- Main Container --- */
        .main .block-container {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 25px;
            padding: 40px;
            margin-top: 20px;
            box-shadow: 
                0 25px 50px rgba(0, 0, 0, 0.1),
                0 0 0 1px rgba(255, 255, 255, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.3);
        }

        /* --- Enhanced Title with Gradient and Animation --- */
        .main-title {
            text-align: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-weight: 900;
            font-size: 3.5em;
            margin-bottom: 20px;
            position: relative;
            animation: titleGlow 3s ease-in-out infinite alternate;
        }

        @keyframes titleGlow {
            0% { filter: drop-shadow(0 0 20px rgba(102, 126, 234, 0.3)); }
            100% { filter: drop-shadow(0 0 30px rgba(102, 126, 234, 0.6)); }
        }

        .main-title::after {
            content: '';
            position: absolute;
            bottom: -10px;
            left: 50%;
            transform: translateX(-50%);
            width: 120px;
            height: 4px;
            background: linear-gradient(90deg, transparent, #667eea, #764ba2, transparent);
            border-radius: 2px;
            animation: shimmer 2s linear infinite;
        }

        @keyframes shimmer {
            0% { opacity: 0.5; transform: translateX(-50%) scaleX(0.8); }
            50% { opacity: 1; transform: translateX(-50%) scaleX(1.2); }
            100% { opacity: 0.5; transform: translateX(-50%) scaleX(0.8); }
        }

        /* --- Enhanced Intro Text with Glassmorphism --- */
        .intro-text {
            font-size: 1.3em;
            color: #2c3e50;
            text-align: center;
            padding: 30px;
            background: rgba(255, 255, 255, 0.7);
            backdrop-filter: blur(15px);
            border-radius: 20px;
            margin: 30px 0;
            border: 1px solid rgba(255, 255, 255, 0.3);
            box-shadow: 
                0 15px 35px rgba(0, 0, 0, 0.1),
                inset 0 1px 0 rgba(255, 255, 255, 0.6);
            position: relative;
            overflow: hidden;
            animation: fadeInUp 0.8s ease-out;
        }

        .intro-text::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: linear-gradient(45deg, transparent, rgba(255, 255, 255, 0.1), transparent);
            animation: shine 3s linear infinite;
        }

        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(30px); }
            to { opacity: 1; transform: translateY(0); }
        }

        @keyframes shine {
            0% { transform: translateX(-100%) translateY(-100%) rotate(45deg); }
            100% { transform: translateX(100%) translateY(100%) rotate(45deg); }
        }

        /* --- Revolutionary Expander Design --- */
        div[data-testid="stExpander"] {
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(255, 255, 255, 0.7) 100%);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 25px;
            box-shadow: 
                0 20px 40px rgba(0, 0, 0, 0.1),
                inset 0 1px 0 rgba(255, 255, 255, 0.6);
            margin: 20px 0;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            overflow: hidden;
            position: relative;
            animation: slideInRight 0.6s ease-out;
        }

        div[data-testid="stExpander"]:nth-child(odd) {
            animation: slideInLeft 0.6s ease-out;
        }

        @keyframes slideInRight {
            from { opacity: 0; transform: translateX(50px); }
            to { opacity: 1; transform: translateX(0); }
        }

        @keyframes slideInLeft {
            from { opacity: 0; transform: translateX(-50px); }
            to { opacity: 1; transform: translateX(0); }
        }

        div[data-testid="stExpander"]:hover {
            transform: translateY(-8px) scale(1.02);
            box-shadow: 
                0 30px 60px rgba(0, 0, 0, 0.15),
                inset 0 1px 0 rgba(255, 255, 255, 0.8);
        }

        /* --- Animated Gradient Border --- */
        div[data-testid="stExpander"]::before {
            content: '';
            position: absolute;
            top: -2px;
            right: -2px;
            left: -2px;
            bottom: -2px;
            background: linear-gradient(45deg, #667eea, #764ba2, #667eea);
            border-radius: 27px;
            z-index: -1;
            animation: rotateBorder 3s linear infinite;
        }

        @keyframes rotateBorder {
            0% { background: linear-gradient(45deg, #667eea, #764ba2, #667eea); }
            33% { background: linear-gradient(45deg, #764ba2, #667eea, #764ba2); }
            66% { background: linear-gradient(45deg, #667eea, #764ba2, #667eea); }
            100% { background: linear-gradient(45deg, #764ba2, #667eea, #764ba2); }
        }

        /* --- Enhanced Expander Header --- */
        div[data-testid="stExpander"] summary {
            font-size: 1.6em !important;
            font-weight: 800;
            background: linear-gradient(135deg, #2c3e50 0%, #4a6741 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            padding: 25px 30px;
            margin: 0;
            position: relative;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        div[data-testid="stExpander"] summary:hover {
            transform: translateX(-5px);
        }

        /* --- Floating Icon Animation --- */
        div[data-testid="stExpander"] summary::before {
            content: '';
            position: absolute;
            right: 30px;
            top: 50%;
            transform: translateY(-50%);
            width: 12px;
            height: 12px;
            background: radial-gradient(circle, #667eea 0%, #764ba2 100%);
            border-radius: 50%;
            box-shadow: 
                0 0 0 0 rgba(102, 126, 234, 0.7),
                0 0 20px rgba(102, 126, 234, 0.3);
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% {
                transform: translateY(-50%) scale(0.95);
                box-shadow: 0 0 0 0 rgba(102, 126, 234, 0.7);
            }
            70% {
                transform: translateY(-50%) scale(1);
                box-shadow: 0 0 0 10px rgba(102, 126, 234, 0);
            }
            100% {
                transform: translateY(-50%) scale(0.95);
                box-shadow: 0 0 0 0 rgba(102, 126, 234, 0);
            }
        }

        /* --- Enhanced Content Area --- */
        div[data-testid="stExpander"] [data-testid="stExpanderDetails"] {
            padding: 30px;
            background: rgba(255, 255, 255, 0.6);
            backdrop-filter: blur(10px);
            border-radius: 0 0 25px 25px;
            position: relative;
        }

        div[data-testid="stExpander"] [data-testid="stExpanderDetails"]::before {
            content: '';
            position: absolute;
            top: 0;
            left: 30px;
            right: 30px;
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(102, 126, 234, 0.3), transparent);
        }

        /* --- Enhanced Section Headers --- */
        .section-content h4 {
            color: #1a5276;
            font-size: 1.4em;
            font-weight: 700;
            margin-top: 30px;
            margin-bottom: 15px;
            position: relative;
            padding-right: 20px;
            transition: all 0.3s ease;
        }

        .section-content h4:hover {
            color: #667eea;
            transform: translateX(-5px);
        }

        .section-content h4::before {
            content: '';
            position: absolute;
            right: 0;
            top: 50%;
            transform: translateY(-50%);
            width: 6px;
            height: 25px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 3px;
            box-shadow: 0 0 15px rgba(102, 126, 234, 0.4);
        }

        /* --- Enhanced Text Styling --- */
        .section-content p, .section-content li {
            font-size: 1.1em !important;
            line-height: 1.9 !important;
            color: #2c3e50;
            font-weight: 400;
            transition: all 0.3s ease;
        }

        .section-content p:hover, .section-content li:hover {
            color: #1a5276;
            transform: translateX(-3px);
        }

        /* --- Enhanced List Styling --- */
        .section-content ul {
            list-style: none;
            padding-right: 0;
            margin-bottom: 25px;
        }

        .section-content li {
            margin-bottom: 15px;
            padding-right: 30px;
            position: relative;
            transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }

        .section-content li::before {
            content: '';
            position: absolute;
            right: 0;
            top: 15px;
            width: 10px;
            height: 10px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 50%;
            box-shadow: 
                0 0 0 0 rgba(102, 126, 234, 0.7),
                0 4px 8px rgba(102, 126, 234, 0.3);
            animation: listPulse 3s infinite;
        }

        @keyframes listPulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.2); box-shadow: 0 0 0 5px rgba(102, 126, 234, 0); }
        }

        /* --- Enhanced Strong Text --- */
        .section-content b, .section-content strong {
            color: #667eea;
            font-weight: 700;
            text-shadow: 0 1px 2px rgba(102, 126, 234, 0.2);
        }

        /* --- Enhanced Contact Links --- */
        .contact-links a {
            text-decoration: none;
            color: #667eea;
            font-weight: 600;
            transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            padding: 8px 15px;
            border-radius: 20px;
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
            border: 1px solid rgba(102, 126, 234, 0.2);
            display: inline-block;
            margin: 2px;
            position: relative;
            overflow: hidden;
        }

        .contact-links a::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
            transition: left 0.5s ease;
        }

        .contact-links a:hover {
            transform: translateY(-2px) scale(1.05);
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
            border-color: #667eea;
        }

        .contact-links a:hover::before {
            left: 100%;
        }

        /* --- Enhanced Custom Divider --- */
        .custom-divider {
            height: 3px;
            background: linear-gradient(90deg, transparent, #667eea, #764ba2, transparent);
            margin: 40px 0;
            border-radius: 2px;
            position: relative;
            overflow: hidden;
        }

        .custom-divider::after {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 50%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.8), transparent);
            animation: dividerShine 2s linear infinite;
        }

        @keyframes dividerShine {
            0% { left: -100%; }
            100% { left: 100%; }
        }

        /* --- Responsive Design --- */
        @media (max-width: 768px) {
            .main-title {
                font-size: 2.5em;
            }
            
            .intro-text {
                font-size: 1.1em;
                padding: 20px;
            }
            
            .main .block-container {
                padding: 20px;
                margin-top: 10px;
            }
            
            div[data-testid="stExpander"] {
                margin: 15px 0;
            }
            
            div[data-testid="stExpander"] summary {
                font-size: 1.3em !important;
                padding: 20px;
            }
        }

        /* --- Loading Animation --- */
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        .stApp {
            animation: fadeIn 0.8s ease-out;
        }

        /* --- Scroll Animations --- */
        div[data-testid="stExpander"] {
            animation-delay: calc(var(--animation-order, 0) * 0.1s);
        }

        div[data-testid="stExpander"]:nth-child(1) { --animation-order: 1; }
        div[data-testid="stExpander"]:nth-child(2) { --animation-order: 2; }
        div[data-testid="stExpander"]:nth-child(3) { --animation-order: 3; }
        div[data-testid="stExpander"]:nth-child(4) { --animation-order: 4; }
        div[data-testid="stExpander"]:nth-child(5) { --animation-order: 5; }
        div[data-testid="stExpander"]:nth-child(6) { --animation-order: 6; }
        div[data-testid="stExpander"]:nth-child(7) { --animation-order: 7; }
        div[data-testid="stExpander"]:nth-child(8) { --animation-order: 8; }
        div[data-testid="stExpander"]:nth-child(9) { --animation-order: 9; }
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
        <p>هذا التطبيق مصمم خصيصاً لمشرفي المجموعات القرائية. أنت، كمشرف، الشخص الوحيد الذي يحتاج إلى استخدام هذه المنصة. أما أعضاء فريقك، فكل ما عليهم فعله هو استخدام رابط Google Form الذي ستوفره لهم لتسجيل قراءاتهم اليومية.</p>
        <p><strong>ببساطة:</strong> أنت تدير وتحلل هنا، وهم يسجلون هناك. الهدف هو منحك القوة التحليلية الكاملة بأقل مجهود ممكن من الأعضاء.</p>
    </div>
    """, unsafe_allow_html=True)


# --- Section 2: آلية عمل التطبيق ---
with st.expander("⚙️ آلية عمل التطبيق: من الإعداد إلى المزامنة"):
    st.markdown("""
    <div class="section-content">
        <p>يعتمد التطبيق على الربط الآمن مع حسابك في جوجل لتسهيل كل شيء. عند إعداد حسابك لأول مرة، يقوم التطبيق تلقائياً بإنشاء جدول بيانات (Google Sheet) ونموذج تسجيل (Google Form) خاصين بك ومملوكين لك بالكامل.</p>
        
        <h4>نموذج التسجيل (Google Form)</h4>
        <p>هو الأداة البسيطة والمباشرة التي يستخدمها أعضاء فريقك لتسجيل قراءاتهم اليومية في أي وقت ومن أي جهاز.</p>
        
        <h4>جدول البيانات (Google Sheet)</h4>
        <p>هو قاعدة البيانات التي يتم فيها تخزين جميع الردود والسجلات بشكل آمن ومنظم في حسابك الخاص على Google Drive.</p>
        
        <h4>المزامنة والتحديث</h4>
        <p>لست بحاجة للدخول إلى التطبيق يومياً. متى ما أردت الاطلاع على آخر النتائج والتحليلات، كل ما عليك فعله هو الضغط على زر "🔄 تحديث وسحب البيانات" الموجود في الشريط الجانبي، وسيقوم التطبيق بسحب آخر البيانات من ملفك، معالجتها، وتحديث جميع الإحصائيات والرسوم البيانية في ثوانٍ.</p>
    </div>
    """, unsafe_allow_html=True)


# --- Section 3: إدارة المشاركين ---
with st.expander("👥 إدارة المشاركين: إضافة وتعطيل"):
    st.markdown("""
    <div class="section-content">
        <h4>إضافة أعضاء جدد</h4>
        <p>يمكنك بسهولة إضافة أعضاء جدد في أي وقت. سيقوم التطبيق تلقائياً بتحديث قائمة الأسماء في نموذج التسجيل (Google Form) ليشملهم فوراً.</p>
        
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
            <li><strong>مؤشرات الأداء الرئيسية:</strong> تعطيك نظرة سريعة وشاملة على أرقام الماراثون الكلية (إجمالي ساعات القراءة، عدد الكتب المنهَاة، إلخ) لتقييم صحة ونشاط المجموعة بشكل عام.</li>
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