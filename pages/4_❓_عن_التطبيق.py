import streamlit as st
import db_manager as db
import auth_manager

st.set_page_config(
    page_title="عن التطبيق",
    page_icon="❓",
    layout="wide"
)

# This CSS snippet enforces RTL and adds custom styles for the new accordion component
st.markdown("""
    <style>
        /* --- Base RTL and Font Fixes --- */
        .stApp { direction: rtl; }
        [data-testid="stSidebar"] { direction: rtl; }
        h1, h2, h3, h4, h5, h6, p, li { text-align: right !important; }

        /* --- Custom Accordion Styles --- */
        .accordion-container {
            width: 100%;
            margin: 0 auto;
        }
        .accordion-item {
            background-color: #ffffff;
            border: 1px solid #e9ecef;
            border-radius: 12px;
            margin-bottom: 15px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            transition: box-shadow 0.3s ease-in-out;
        }
        .accordion-item:hover {
            box-shadow: 0 6px 16px rgba(0, 0, 0, 0.08);
        }
        
        /* Hide the default checkbox */
        .accordion-item input[type="checkbox"] {
            display: none;
        }
        
        /* The clickable title label */
        .accordion-title {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 25px;
            font-size: 1.4em;
            font-weight: bold;
            color: #2c3e50;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }
        
        .accordion-title:hover {
            background-color: #f8f9fa;
        }
        
        /* The icon/arrow */
        .accordion-title::before {
            content: '▼';
            font-size: 0.8em;
            transition: transform 0.4s ease;
            color: #3498db;
        }
        
        /* The content that expands */
        .accordion-content {
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.5s ease-out, padding 0.5s ease-out;
            padding: 0 25px;
            background-color: #ffffff;
            border-bottom-left-radius: 12px;
            border-bottom-right-radius: 12px;
        }
        
        /* --- Logic for opening the accordion --- */
        .accordion-item input[type="checkbox"]:checked ~ .accordion-title {
            background-color: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
        }
        
        .accordion-item input[type="checkbox"]:checked ~ .accordion-title::before {
            transform: rotate(180deg);
        }
        
        .accordion-item input[type="checkbox"]:checked ~ .accordion-content {
            max-height: 2000px; /* Adjust as needed */
            padding: 25px;
        }
        
        /* --- Styles for the content inside the accordion --- */
        .content-section h4 {
            color: #1a5276;
            font-size: 1.25em;
            font-weight: bold;
            border-bottom: 2px solid #aed6f1;
            padding-bottom: 8px;
            margin-top: 10px;
            margin-bottom: 20px;
        }
        .content-section p {
            font-size: 1.1em !important;
            line-height: 1.9 !important;
            color: #34495e;
            margin-bottom: 15px;
        }
        .content-section ul {
            list-style-position: outside;
            padding-right: 20px;
            margin: 0;
        }
        .content-section li {
            font-size: 1.05em !important;
            line-height: 1.9 !important;
            margin-bottom: 12px;
            padding-right: 10px;
        }
        .content-section li::marker {
            color: #3498db;
            font-size: 1.1em;
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
st.markdown("<p style='font-size: 1.2em; text-align: center; color: #5D6D7E;'>أهلاً بك في الدليل الشامل! هنا، ستجد كل ما تحتاج لمعرفته حول كيفية عمل التطبيق، من فلسفة النقاط إلى شرح الألقاب والأخبار.</p>", unsafe_allow_html=True)


# --- Build the entire page HTML as a single string ---

page_html = """
<div class="accordion-container">
    <!-- Section 1: Philosophy of Points -->
    <div class="accordion-item">
        <input type="checkbox" id="accordion-1" name="accordion-group" checked>
        <label for="accordion-1" class="accordion-title">🎯 نظام المسابقات والنقاط: فلسفة التحفيز الذكي</label>
        <div class="accordion-content">
            <div class="content-section">
                <p>هذا هو قلب المشروع النابض، وهو مصمم لتحقيق توازن دقيق بين القراءة الجماعية المنظمة والقراءة الفردية الحرة، لخلق جو حماسي ومرن.</p>
                <h4>حرية الاختيار هي الأساس</h4>
                <p>لا يوجد مسار إلزامي. العضو لديه الحرية الكاملة ليختار المسار الذي يناسبه:</p>
                <ul>
                    <li><b>مسار الكتاب المشترك:</b> يقرأ الكتاب الذي تم اختياره للتحدي. إنهاؤه يمنحه <strong>دفعة هائلة من النقاط</strong> تقديرًا لالتزامه وتهيئته لجلسة النقاش.</li>
                    <li><b>مسار الكتاب الحر:</b> يقرأ أي كتاب آخر من اختياره. هنا، تتضاعف نقاطه بناءً على <strong>وقت القراءة</strong>، لكن نقاط إنهاء الكتاب تكون أقل.</li>
                </ul>
                <p>ويمكن للعضو أن يمشي بالمسارين معًا في وقت واحد، أو حتى يقرأ عدة كتب حرة! الأمر متروك له ولهمّته.</p>
                <h4>منطق النقاط الذكي للموازنة</h4>
                <ul>
                    <li><b>للتشجيع على الالتزام:</b> نقاط إنهاء الكتاب المشترك <strong>أعلى بكثير</strong>.</li>
                    <li><b>لتعزيز المشاركة المجتمعية:</b> حضور جلسة النقاش الخاصة بالكتاب المشترك يمنح نقاطًا إضافية.</li>
                    <li><b>لتشجيع القراءة العميقة:</b> إضافة <strong>اقتباس</strong> من كتاب يقرأه العضو يمنحه نقاطًا إضافية.</li>
                </ul>
            </div>
        </div>
    </div>

    <!-- Section 2: Hall of Fame Explained -->
    <div class="accordion-item">
        <input type="checkbox" id="accordion-2" name="accordion-group">
        <label for="accordion-2" class="accordion-title">🌟 فك شفرة الأبطال: شرح لوحة الشرف</label>
        <div class="accordion-content">
            <div class="content-section">
                <p>لوحة شرف الأبطال هي احتفاء بالإنجازات المتميزة في الماراثون. إليك معنى كل لقب:</p>
                <ul>
                    <li><b>🧠 العقل المدبّر:</b> يُمنح للعضو الذي جمع <strong>أعلى عدد من النقاط</strong> في المجموع الكلي.</li>
                    <li><b>⏳ سيد الساعات:</b> يُمنح للعضو الذي سجل <strong>أطول وقت قراءة إجمالي</strong>.</li>
                    <li><b>📚 الديدان القارئ:</b> يُمنح للعضو الذي <strong>أنهى أكبر عدد من الكتب</strong>.</li>
                    <li><b>💎 صائد الدرر:</b> يُمنح للعضو الذي أرسل <strong>أكبر عدد من الاقتباسات</strong>.</li>
                    <li><b>🏃‍♂️ صاحب النَفَس الطويل:</b> يُمنح للعضو الذي سجل القراءة في <strong>أكبر عدد من الأيام المختلفة</strong>.</li>
                    <li><b>⚡ العدّاء السريع:</b> يُمنح للعضو الذي سجل <strong>أعلى عدد من دقائق القراءة في يوم واحد</strong>.</li>
                    <li><b>⭐ نجم الأسبوع:</b> يُمنح للعضو الذي سجل <strong>أعلى مجموع دقائق قراءة خلال أسبوع واحد</strong>.</li>
                    <li><b>💪 عملاق الشهر:</b> يُمنح للعضو الذي سجل <strong>أعلى مجموع دقائق قراءة خلال شهر واحد</strong>.</li>
                </ul>
            </div>
        </div>
    </div>

    <!-- Section 3: News Ticker Explained -->
    <div class="accordion-item">
        <input type="checkbox" id="accordion-3" name="accordion-group">
        <label for="accordion-3" class="accordion-title">📰 نشرة الماراثون: كيف تعمل "آخر الأخبار"؟</label>
        <div class="accordion-content">
            <div class="content-section">
                <p>شريط الأخبار هو نافذتك على أحدث المستجدات في الماراثون، ويعمل بطريقتين مختلفتين حسب الصفحة:</p>
                <h4>في لوحة التحكم العامة</h4>
                <ul>
                    <li>يعرض الشريط هنا <strong>التغييرات التي طرأت على لوحة شرف الأبطال خلال آخر 7 أيام</strong>.</li>
                    <li>يقوم النظام بمقارنة قائمة الأبطال الحالية بقائمتهم قبل أسبوع، ويرصد أي تغييرات.</li>
                    <li>الهدف هو تسليط الضوء على الديناميكية والمنافسة على مستوى الماراثون ككل.</li>
                </ul>
                <h4>في صفحة تحليلات التحديات</h4>
                <ul>
                    <li>يركز الشريط هنا على <strong>أحداث التحدي المحدد فقط</strong>.</li>
                    <li>يعرض الأخبار بتسلسل زمني، مع التركيز على آخر المستجدات (مثل من أنهى الكتاب ومتى).</li>
                    <li>الهدف هو متابعة التقدم والإنجازات داخل كل تحدي على حدة.</li>
                </ul>
            </div>
        </div>
    </div>

    <!-- Section 4: Q&A -->
    <div class="accordion-item">
        <input type="checkbox" id="accordion-4" name="accordion-group">
        <label for="accordion-4" class="accordion-title">🤔 أسئلة شائعة</label>
        <div class="accordion-content">
            <div class="content-section">
                <h4>كيف يتم حساب النقاط بالضبط؟</h4>
                <p>يتم حساب النقاط بناءً على نظام النقاط الافتراضي الذي يمكنك تعديله. يمكنك مراجعة نظام النقاط الحالي من صفحة "الإدارة والإعدادات".</p>
                <h4>هل يمكنني تعديل نظام النقاط؟</h4>
                <p>نعم! كمدير للماراثون، يمكنك الذهاب إلى صفحة "الإدارة والإعدادات" وتعديل نظام النقاط الافتراضي، أو تعيين نظام نقاط خاص لكل تحدي على حدة.</p>
                <h4>ماذا لو نسيت تسجيل قراءتي ليوم ما؟</h4>
                <p>لا تقلق. يمكن لمدير الماراثون الذهاب إلى "الإدارة والإعدادات" ثم "محرر السجلات" لتعديل أي سجل سابق لأي عضو. بعد الحفظ، يجب إعادة مزامنة البيانات لتعكس التغييرات.</p>
            </div>
        </div>
    </div>
    
    <!-- Section 5: About the Developer -->
    <div class="accordion-item">
        <input type="checkbox" id="accordion-5" name="accordion-group">
        <label for="accordion-5" class="accordion-title">🧑‍💻 عن المطور</label>
        <div class="accordion-content">
            <div class="content-section contact-links">
                <p><strong>الاسم:</strong> احمد نايفه</p>
                <p><strong>الهدف من المشروع:</strong> يهدف هذا المشروع إلى توفير أداة عصرية ومحفزة للمجموعات القرائية في الوطن العربي، للمساهمة في تعزيز ثقافة القراءة وجعلها تجربة تفاعلية وممتعة.</p>
                <h4><strong>للتواصل والدعم الفني</strong></h4>
                <p>إذا واجهتك أي مشكلة تقنية، أو كان لديك اقتراح لتطوير التطبيق، فلا تتردد في التواصل معي:</p>
                <ul>
                    <li><strong>البريد الإلكتروني:</strong> <a href="mailto:ahmadnayfeh2000@gmail.com">ahmadnayfeh2000@gmail.com</a></li>
                    <li><strong>Portfolio:</strong> <a href="https://ahmadnayfeh.vercel.app/" target="_blank">ahmadnayfeh.vercel.app</a></li>
                    <li><strong>LinkedIn:</strong> <a href="https://www.linkedin.com/in/ahmad-nayfeh2000/" target="_blank">in/ahmad-nayfeh2000</a></li>
                    <li><strong>GitHub:</strong> <a href="https://github.com/Ahmad-Nayfeh" target="_blank">Ahmad-Nayfeh</a></li>
                </ul>
            </div>
        </div>
    </div>
</div>
"""

# Display the entire accordion with a single markdown command
st.markdown(page_html, unsafe_allow_html=True)
