import streamlit as st
import db_manager as db
import auth_manager

# إعداد صفحة التطبيق
st.set_page_config(
    page_title="عن التطبيق",
    page_icon="❓",
    layout="wide"
)

def load_custom_css():
    """تحميل الأنماط المخصصة للصفحة"""
    return """
    <style>
        /* --- إعدادات RTL والخط الأساسية --- */
        .stApp { 
            direction: rtl; 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        [data-testid="stSidebar"] { direction: rtl; }
        h1, h2, h3, h4, h5, h6, p, li { 
            text-align: right !important; 
        }

        /* --- أنماط الأكورديون المخصصة --- */
        .accordion-container {
            width: 100%;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px 0;
        }
        
        .accordion-item {
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            border: 1px solid #e9ecef;
            border-radius: 16px;
            margin-bottom: 20px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
            transition: all 0.3s ease;
            overflow: hidden;
        }
        
        .accordion-item:hover {
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
            transform: translateY(-2px);
        }
        
        /* إخفاء checkbox الافتراضي */
        .accordion-item input[type="checkbox"] {
            display: none;
        }
        
        /* عنوان الأكورديون القابل للنقر */
        .accordion-title {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 24px 30px;
            font-size: 1.3em;
            font-weight: 700;
            color: #2c3e50;
            cursor: pointer;
            transition: all 0.3s ease;
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            border-bottom: 1px solid transparent;
        }
        
        .accordion-title:hover {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            color: #1a5276;
        }
        
        /* أيقونة السهم */
        .accordion-title::before {
            content: '▼';
            font-size: 0.9em;
            transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            color: #3498db;
            font-weight: bold;
        }
        
        /* محتوى الأكورديون */
        .accordion-content {
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.5s cubic-bezier(0.4, 0, 0.2, 1);
            background: #ffffff;
        }
        
        /* --- حالة الأكورديون المفتوح --- */
        .accordion-item input[type="checkbox"]:checked ~ .accordion-title {
            background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
            color: white;
            border-bottom: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .accordion-item input[type="checkbox"]:checked ~ .accordion-title::before {
            transform: rotate(180deg);
            color: white;
        }
        
        .accordion-item input[type="checkbox"]:checked ~ .accordion-content {
            max-height: 3000px;
            padding: 30px;
        }
        
        /* --- أنماط المحتوى الداخلي --- */
        .content-section {
            line-height: 1.8;
        }
        
        .content-section h4 {
            color: #1a5276;
            font-size: 1.3em;
            font-weight: 700;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin: 25px 0 20px 0;
            position: relative;
        }
        
        .content-section h4::after {
            content: '';
            position: absolute;
            bottom: -3px;
            right: 0;
            width: 50px;
            height: 3px;
            background: linear-gradient(90deg, #3498db, #2980b9);
        }
        
        .content-section p {
            font-size: 1.1em !important;
            line-height: 1.9 !important;
            color: #2c3e50;
            margin-bottom: 18px;
            text-align: justify;
        }
        
        .content-section ul {
            list-style: none;
            padding-right: 0;
            margin: 20px 0;
        }
        
        .content-section li {
            font-size: 1.05em !important;
            line-height: 1.8 !important;
            margin-bottom: 15px;
            padding-right: 25px;
            position: relative;
            color: #34495e;
        }
        
        .content-section li::before {
            content: '🔹';
            position: absolute;
            right: 0;
            color: #3498db;
            font-size: 1.2em;
        }
        
        .content-section b, .content-section strong {
            color: #1a5276;
            font-weight: 700;
        }
        
        /* --- أنماط روابط التواصل --- */
        .contact-links a {
            color: #2980b9;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.3s ease;
            border-bottom: 1px solid transparent;
        }
        
        .contact-links a:hover {
            color: #3498db;
            border-bottom: 1px solid #3498db;
            transform: translateY(-1px);
        }
        
        /* --- أنماط الهيدر --- */
        .page-header {
            text-align: center;
            padding: 40px 0;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            margin-bottom: 40px;
            border-radius: 20px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        }
        
        .page-header h1 {
            color: #1a5276;
            font-size: 2.5em;
            margin-bottom: 15px;
            font-weight: 800;
        }
        
        .page-header p {
            color: #5D6D7E;
            font-size: 1.2em;
            max-width: 800px;
            margin: 0 auto;
            line-height: 1.6;
        }
        
        /* --- تحسينات الاستجابة --- */
        @media (max-width: 768px) {
            .accordion-title {
                padding: 20px 20px;
                font-size: 1.1em;
            }
            
            .accordion-content {
                padding: 20px;
            }
            
            .content-section h4 {
                font-size: 1.2em;
            }
            
            .content-section p, .content-section li {
                font-size: 1em !important;
            }
            
            .page-header h1 {
                font-size: 2em;
            }
            
            .page-header p {
                font-size: 1.1em;
            }
        }
    </style>
    """

def get_accordion_sections():
    """إرجاع أقسام الأكورديون كقائمة منظمة"""
    return [
        {
            "id": "points-system",
            "title": "🎯 نظام المسابقات والنقاط: فلسفة التحفيز الذكي",
            "content": """
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
            """,
            "default_open": True
        },
        {
            "id": "hall-of-fame",
            "title": "🌟 فك شفرة الأبطال: شرح لوحة الشرف",
            "content": """
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
            """,
            "default_open": False
        },
        {
            "id": "news-ticker",
            "title": "📰 نشرة الماراثون: كيف تعمل آخر الأخبار؟",
            "content": """
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
            """,
            "default_open": False
        },
        {
            "id": "faq",
            "title": "🤔 أسئلة شائعة",
            "content": """
                <div class="content-section">
                    <h4>كيف يتم حساب النقاط بالضبط؟</h4>
                    <p>يتم حساب النقاط بناءً على نظام النقاط الافتراضي الذي يمكنك تعديله. يمكنك مراجعة نظام النقاط الحالي من صفحة "الإدارة والإعدادات".</p>
                    <h4>هل يمكنني تعديل نظام النقاط؟</h4>
                    <p>نعم! كمدير للماراثون، يمكنك الذهاب إلى صفحة "الإدارة والإعدادات" وتعديل نظام النقاط الافتراضي، أو تعيين نظام نقاط خاص لكل تحدي على حدة.</p>
                    <h4>ماذا لو نسيت تسجيل قراءتي ليوم ما؟</h4>
                    <p>لا تقلق. يمكن لمدير الماراثون الذهاب إلى "الإدارة والإعدادات" ثم "محرر السجلات" لتعديل أي سجل سابق لأي عضو. بعد الحفظ، يجب إعادة مزامنة البيانات لتعكس التغييرات.</p>
                    <h4>كيف أضيف اقتباساً من كتاب؟</h4>
                    <p>يمكنك إضافة اقتباس من خلال صفحة "تسجيل القراءة" عند إضافة جلسة قراءة جديدة. الاقتباسات تمنحك نقاطاً إضافية وتساهم في إثراء المحتوى.</p>
                    <h4>هل يمكنني قراءة أكثر من كتاب في نفس الوقت؟</h4>
                    <p>بالطبع! يمكنك قراءة الكتاب المشترك للتحدي إلى جانب أي عدد من الكتب الحرة. كل كتاب يُحسب بشكل منفصل.</p>
                </div>
            """,
            "default_open": False
        },
        {
            "id": "developer",
            "title": "🧑‍💻 عن المطور",
            "content": """
                <div class="content-section contact-links">
                    <p><strong>الاسم:</strong> أحمد نايفه</p>
                    <p><strong>الهدف من المشروع:</strong> يهدف هذا المشروع إلى توفير أداة عصرية ومحفزة للمجموعات القرائية في الوطن العربي، للمساهمة في تعزيز ثقافة القراءة وجعلها تجربة تفاعلية وممتعة.</p>
                    <h4>للتواصل والدعم الفني</h4>
                    <p>إذا واجهتك أي مشكلة تقنية، أو كان لديك اقتراح لتطوير التطبيق، فلا تتردد في التواصل معي:</p>
                    <ul>
                        <li><strong>البريد الإلكتروني:</strong> <a href="mailto:ahmadnayfeh2000@gmail.com">ahmadnayfeh2000@gmail.com</a></li>
                        <li><strong>الموقع الشخصي:</strong> <a href="https://ahmadnayfeh.vercel.app/" target="_blank">ahmadnayfeh.vercel.app</a></li>
                        <li><strong>LinkedIn:</strong> <a href="https://www.linkedin.com/in/ahmad-nayfeh2000/" target="_blank">in/ahmad-nayfeh2000</a></li>
                        <li><strong>GitHub:</strong> <a href="https://github.com/Ahmad-Nayfeh" target="_blank">Ahmad-Nayfeh</a></li>
                    </ul>
                    <p><em>ملاحظة: هذا المشروع مفتوح المصدر ومتاح للجميع للاستخدام والتطوير!</em></p>
                </div>
            """,
            "default_open": False
        }
    ]

def generate_accordion_html(sections):
    """إنشاء HTML للأكورديون بناءً على الأقسام"""
    accordion_html = '<div class="accordion-container">'
    
    for section in sections:
        checked = "checked" if section["default_open"] else ""
        accordion_html += f"""
        <div class="accordion-item">
            <input type="checkbox" id="{section['id']}" name="accordion-group" {checked}>
            <label for="{section['id']}" class="accordion-title">{section['title']}</label>
            <div class="accordion-content">
                {section['content']}
            </div>
        </div>
        """
    
    accordion_html += '</div>'
    return accordion_html

def authenticate_user():
    """التحقق من صحة المستخدم"""
    creds = auth_manager.authenticate()
    user_id = st.session_state.get('user_id')
    
    if not creds or not user_id:
        st.error("🔐 مصادقة المستخدم مطلوبة. يرجى العودة إلى الصفحة الرئيسية وتسجيل الدخول.")
        st.stop()
    
    return creds, user_id

def display_page_header():
    """عرض رأس الصفحة"""
    st.markdown("""
        <div class="page-header">
            <h1>❓ عن تطبيق ماراثون القراءة</h1>
            <p>أهلاً بك في الدليل الشامل! هنا، ستجد كل ما تحتاج لمعرفته حول كيفية عمل التطبيق، من فلسفة النقاط إلى شرح الألقاب والأخبار.</p>
        </div>
    """, unsafe_allow_html=True)

def main():
    """الوظيفة الرئيسية للتطبيق"""
    try:
        # تحميل الأنماط المخصصة
        st.markdown(load_custom_css(), unsafe_allow_html=True)
        
        # التحقق من صحة المستخدم
        creds, user_id = authenticate_user()
        
        # عرض رأس الصفحة
        display_page_header()
        
        # الحصول على أقسام الأكورديون
        sections = get_accordion_sections()
        
        # إنشاء وعرض HTML للأكورديون
        accordion_html = generate_accordion_html(sections)
        st.markdown(accordion_html, unsafe_allow_html=True)
        
        # إضافة footer
        st.markdown("---")
        st.markdown("""
            <div style="text-align: center; color: #7f8c8d; margin-top: 40px;">
                <p>شكرًا لك على استخدام تطبيق ماراثون القراءة! 📚✨</p>
                <p style="font-size: 0.9em;">نسعى دائماً لتطوير التطبيق وتحسين تجربتك</p>
            </div>
        """, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"❌ حدث خطأ في تحميل الصفحة: {str(e)}")
        st.error("يرجى المحاولة مرة أخرى أو التواصل مع المطور.")

if __name__ == "__main__":
    main()