import streamlit as st
import pandas as pd
from datetime import date, timedelta
import db_manager as db
import plotly.express as px
import plotly.graph_objects as go
from pdf_reporter import PDFReporter
import auth_manager # <-- استيراد مدير المصادقة

st.set_page_config(
    page_title="لوحة التحكم العامة",
    page_icon="📈",
    layout="wide"
)

# Enhanced CSS for stunning professional dashboard
st.markdown("""
    <style>
        /* Import Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        /* Main app container */
        .stApp {
            direction: rtl;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            font-family: 'Inter', sans-serif;
        }
        
        /* Main content styling */
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            background: rgba(255, 255, 255, 0.02);
            border-radius: 20px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            margin: 1rem;
        }
        
        /* Sidebar */
        [data-testid="stSidebar"] {
            direction: rtl;
            background: linear-gradient(180deg, #1e3c72 0%, #2a5298 100%);
        }
        
        /* Header styling */
        h1, h2, h3, h4, h5, h6 {
            color: #ffffff !important;
            font-weight: 600 !important;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }
        
        /* Subheader styling */
        .stSubheader {
            background: linear-gradient(90deg, #ff6b6b, #4ecdc4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 700 !important;
            font-size: 1.8rem !important;
            margin-bottom: 1.5rem !important;
        }
        
        /* Text alignment */
        h1, h2, h3, h4, h5, h6, p, li, .st-bk, .st-b8, .st-b9, .st-ae {
            text-align: right !important;
        }
        
        /* Fix for form controls */
        .st-b8 label, .st-ae label {
            text-align: right !important;
            display: block;
            color: #ffffff !important;
        }
        
        /* Enhanced main KPI cards */
        .main-kpi-card {
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            border-radius: 20px;
            padding: 2rem;
            text-align: center;
            border: none;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .main-kpi-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #ff6b6b, #4ecdc4, #45b7d1);
            border-radius: 20px 20px 0 0;
        }
        
        .main-kpi-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0, 0, 0, 0.15);
        }
        
        .main-kpi-card .label {
            font-size: 1.1rem;
            font-weight: 500;
            color: #6c757d;
            margin-bottom: 0.5rem;
        }
        
        .main-kpi-card .value {
            font-size: 2.8rem;
            font-weight: 700;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 0.5rem 0;
            text-shadow: none;
        }
        
        /* Enhanced hero metric cards */
        .metric-card {
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            border-radius: 16px;
            padding: 1.5rem;
            text-align: center;
            border: none;
            margin-bottom: 1rem;
            height: 140px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.08);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .metric-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, #ff9a9e, #fecfef, #fecfef);
        }
        
        .metric-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 12px 30px rgba(0, 0, 0, 0.12);
        }
        
        .metric-card .label {
            font-size: 1rem;
            font-weight: 600;
            color: #495057;
            margin-bottom: 0.5rem;
        }
        
        .metric-card .value {
            font-size: 1.3rem;
            font-weight: 600;
            color: #212529;
            margin-bottom: 0.25rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        .metric-card .sub-value {
            font-size: 0.9rem;
            color: #6c757d;
            font-weight: 500;
        }
        
        /* Dynamic headline styling */
        .dynamic-headline {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            border-radius: 16px;
            text-align: center;
            font-size: 1.2rem;
            font-weight: 500;
            margin: 2rem 0;
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .dynamic-headline span {
            font-weight: 700;
            color: #ffd700 !important;
        }
        
        /* Section dividers */
        .section-divider {
            height: 2px;
            background: linear-gradient(90deg, transparent, #ff6b6b, #4ecdc4, transparent);
            margin: 3rem 0;
            border-radius: 1px;
        }
        
        /* Chart containers */
        .chart-container {
            background: rgba(255, 255, 255, 0.95);
            padding: 1.5rem;
            border-radius: 16px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.08);
            margin-bottom: 1rem;
        }
        
        .chart-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: #495057;
            margin-bottom: 1rem;
            text-align: center;
        }
        
        /* Info messages */
        .stInfo {
            background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
            color: white;
            border-radius: 12px;
            border: none;
        }
        
        /* Buttons */
        .stButton > button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 12px;
            font-weight: 600;
            padding: 0.75rem 2rem;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
        }
        
        /* Expander */
        .streamlit-expanderHeader {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white !important;
            border-radius: 12px;
            font-weight: 600;
        }
        
        .streamlit-expanderContent {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 0 0 12px 12px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        }
        
        /* Spinner */
        .stSpinner {
            color: #667eea !important;
        }
        
        /* Download button */
        .stDownloadButton > button {
            background: linear-gradient(135deg, #00b894 0%, #00a085 100%);
            color: white;
            border: none;
            border-radius: 12px;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .stDownloadButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0, 184, 148, 0.4);
        }
        
        /* Toast messages */
        .stToast {
            background: linear-gradient(135deg, #00b894 0%, #00a085 100%);
            border-radius: 12px;
        }
        
        /* Responsive design */
        @media (max-width: 768px) {
            .main-kpi-card {
                padding: 1.5rem;
            }
            
            .main-kpi-card .value {
                font-size: 2.2rem;
            }
            
            .metric-card {
                height: 120px;
                padding: 1rem;
            }
            
            .dynamic-headline {
                font-size: 1rem;
                padding: 1.5rem;
            }
        }
    </style>
""", unsafe_allow_html=True)


# --- 1. UNIFIED AUTHENTICATION BLOCK ---
creds = auth_manager.authenticate()
user_id = st.session_state.get('user_id')

if not creds or not user_id:
    st.error("مصادقة المستخدم مطلوبة. يرجى العودة إلى الصفحة الرئيسية وتسجيل الدخول.")
    st.stop()
# -----------------------------------------


# --- Helper function for Dynamic Headline (Overall Dashboard) ---
def generate_headline(logs_df, achievements_df, members_df):
    if 'common_book_minutes' in logs_df.columns and 'other_book_minutes' in logs_df.columns:
        logs_df['total_minutes'] = logs_df['common_book_minutes'] + logs_df['other_book_minutes']
    else:
        return "صفحة جديدة في ماراثوننا، الأسبوع الأول هو صفحة بيضاء، حان وقت تدوين الإنجازات"

    today = date.today()
    last_7_days_start = today - timedelta(days=6)
    prev_7_days_start = today - timedelta(days=13)
    prev_7_days_end = today - timedelta(days=7)

    # Ensure 'submission_date_dt' is datetime before comparison
    logs_df['submission_date_dt'] = pd.to_datetime(logs_df['submission_date_dt'])
    last_7_days_logs = logs_df[logs_df['submission_date_dt'].dt.date >= last_7_days_start]
    prev_7_days_logs = logs_df[(logs_df['submission_date_dt'].dt.date >= prev_7_days_start) & (logs_df['submission_date_dt'].dt.date <= prev_7_days_end)]
    
    last_7_total_minutes = last_7_days_logs['total_minutes'].sum()
    prev_7_total_minutes = prev_7_days_logs['total_minutes'].sum()

    momentum_available = prev_7_total_minutes > 0
    momentum_positive = None
    percentage_change = 0
    if momentum_available:
        percentage_change = ((last_7_total_minutes - prev_7_total_minutes) / prev_7_total_minutes) * 100
        momentum_positive = percentage_change >= 0

    achievements_df['achievement_date_dt'] = pd.to_datetime(achievements_df['achievement_date_dt'])
    recent_achievements = achievements_df[achievements_df['achievement_date_dt'].dt.date >= last_7_days_start]
    book_finishers = recent_achievements[recent_achievements['achievement_type'].isin(['FINISHED_COMMON_BOOK', 'FINISHED_OTHER_BOOK'])]
    
    recent_finishers_names = []
    if not book_finishers.empty and 'member_id' in book_finishers.columns and not members_df.empty:
        finisher_ids = book_finishers['member_id'].unique()
        recent_finishers_names = members_df[members_df['members_id'].isin(finisher_ids)]['name'].tolist()

    achievement_available = len(recent_finishers_names) > 0
    
    highlight_style = "color: #ffd700; font-weight: bold; text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);"

    momentum_str = ""
    if momentum_available:
        if momentum_positive:
            momentum_str = f"الفريق في أوج حماسه، ارتفع الأداء بنسبة <span style='{highlight_style}'>{percentage_change:.0f}%</span> هذا الأسبوع"
        else:
            momentum_str = f"هل أخذ الفريق استراحة محارب، تراجع الأداء بنسبة <span style='{highlight_style}'>{abs(percentage_change):.0f}%</span> هذا الأسبوع"
    
    achievement_str = ""
    if achievement_available:
        n = len(recent_finishers_names)
        names = [f"<span style='{highlight_style}'>{name}</span>" for name in recent_finishers_names]
        if n == 1:
            achievement_detail = f"ونهنئ {names[0]} على إنهائه لكتاب خلال السبع أيام الماضية"
        elif n == 2:
            achievement_detail = f"ونهنئ {names[0]} و {names[1]} على إنهاء كل واحد منهما لكتاب خلال السبع أيام الماضية"
        elif n == 3:
            achievement_detail = f"ونهنئ {names[0]} و {names[1]} و {names[2]} على إنهاء كل واحد منهم لكتاب خلال السبع أيام الماضية"
        elif n == 4:
            achievement_detail = f"ونهنئ {names[0]} و {names[1]} وعضوان آخران على إنهاء كل واحد منهم لكتاب خلال السبع أيام الماضية"
        elif 5 <= n <= 10:
            achievement_detail = f"ونهنئ {names[0]} و {names[1]} و <span style='{highlight_style}'>{n-2}</span> أعضاء آخرين على إنهاء كل واحد منهم لكتاب خلال السبع أيام الماضية"
        else: # n >= 11
            achievement_detail = f"ونحب أن نهنئ أكثر من <span style='{highlight_style}'>{n-1}</span> عضو على إنهائهم لكتاب خلال السبع أيام الماضية"
        
        if not momentum_available:
            achievement_str = f"انطلقت شرارة التحدي، {achievement_detail}"
        else:
            achievement_str = achievement_detail
    
    if momentum_str and achievement_str:
        final_text = f"{momentum_str}، {achievement_str}"
    elif momentum_str:
        final_text = momentum_str
    elif achievement_str:
        final_text = achievement_str
    else:
        final_text = "صفحة جديدة في ماراثوننا، الأسبوع الأول هو صفحة بيضاء، حان وقت تدوين الإنجازات"

    return final_text


# --- Data Loading ---
@st.cache_data(ttl=300)
def load_all_data(user_id):
    all_data = db.get_all_data_for_stats(user_id)
    members_df = pd.DataFrame(all_data.get('members', []))
    periods_df = pd.DataFrame(all_data.get('periods', []))
    logs_df = pd.DataFrame(all_data.get('logs', []))
    achievements_df = pd.DataFrame(all_data.get('achievements', []))
    member_stats_df = db.get_subcollection_as_df(user_id, 'member_stats')
    return members_df, periods_df, logs_df, achievements_df, member_stats_df

members_df, periods_df, logs_df, achievements_df, member_stats_df = load_all_data(user_id)

# --- Data Processing ---
if not logs_df.empty:
    logs_df['submission_date_dt'] = pd.to_datetime(logs_df['submission_date'], format='%d/%m/%Y', errors='coerce')
    logs_df['total_minutes'] = logs_df['common_book_minutes'] + logs_df['other_book_minutes']

if not achievements_df.empty:
    achievements_df['achievement_date_dt'] = pd.to_datetime(achievements_df['achievement_date'], errors='coerce')
    
if not member_stats_df.empty and not members_df.empty:
    member_stats_df.rename(columns={'member_stats_id': 'members_id'}, inplace=True, errors='ignore')
    member_stats_df = pd.merge(member_stats_df, members_df[['members_id', 'name']], on='members_id', how='left')


# --- Page Rendering ---
st.markdown("<h1 style='text-align: center; font-size: 3rem; margin-bottom: 2rem;'>📈 لوحة التحكم العامة</h1>", unsafe_allow_html=True)

# --- Dynamic Headline ---
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
if not logs_df.empty and not achievements_df.empty and not members_df.empty:
    headline_html = generate_headline(logs_df.copy(), achievements_df.copy(), members_df.copy())
    st.markdown(f"<div class='dynamic-headline'>{headline_html}</div>", unsafe_allow_html=True)
else:
    st.markdown("<div class='dynamic-headline'>انطلق الماراثون! أهلاً بكم</div>", unsafe_allow_html=True)
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)


# --- Main KPIs Section ---
st.markdown("<h2 style='text-align: center; margin-bottom: 2rem;'>📊 مؤشرات الأداء الرئيسية</h2>", unsafe_allow_html=True)

def display_main_kpi(col, label, value):
    with col:
        st.markdown(f"""
        <div class="main-kpi-card">
            <div class="label">{label}</div>
            <div class="value">{value}</div>
        </div>
        """, unsafe_allow_html=True)

kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
kpi_col4, kpi_col5, kpi_col6 = st.columns(3)

# Calculate KPIs
total_hours_val = 0
total_books_finished_val = 0
total_quotes_val = 0
active_members_count_val = 0
total_reading_days_val = 0
completed_challenges_count_val = 0

if not member_stats_df.empty:
    total_minutes = member_stats_df['total_reading_minutes_common'].sum() + member_stats_df['total_reading_minutes_other'].sum()
    total_hours_val = f"{int(total_minutes // 60):,}"
    total_books_finished_val = f"{int(member_stats_df['total_common_books_read'].sum() + member_stats_df['total_other_books_read'].sum()):,}"
    total_quotes_val = f"{int(member_stats_df['total_quotes_submitted'].sum()):,}"

if not members_df.empty:
    active_members_count_val = f"{len(members_df[members_df['is_active'] == True])}"

if not logs_df.empty:
    total_reading_days_val = f"{logs_df['submission_date_dt'].nunique()}"

if not periods_df.empty:
    today_date = date.today()
    periods_df['end_date_dt'] = pd.to_datetime(periods_df['end_date']).dt.date
    completed_challenges_count_val = f"{len(periods_df[periods_df['end_date_dt'] < today_date])}"

# Display KPIs
display_main_kpi(kpi_col1, "⏳ إجمالي ساعات القراءة", total_hours_val)
display_main_kpi(kpi_col2, "📚 إجمالي الكتب المنهَاة", total_books_finished_val)
display_main_kpi(kpi_col3, "✍️ إجمالي الاقتباسات", total_quotes_val)
display_main_kpi(kpi_col4, "👥 الأعضاء النشطون", active_members_count_val)
display_main_kpi(kpi_col5, "🗓️ إجمالي أيام القراءة", total_reading_days_val)
display_main_kpi(kpi_col6, "🏁 التحديات المكتملة", completed_challenges_count_val)
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)


# --- Hall of Fame Section ---
st.markdown("<h2 style='text-align: center; margin-bottom: 2rem;'>🌟 لوحة شرف الأبطال</h2>", unsafe_allow_html=True)

def display_hero(col, title, name, value_str):
    with col:
        st.markdown(f"""
        <div class="metric-card">
            <div class="label">{title}</div>
            <div class="value">{name}</div>
            <div class="sub-value">{value_str}</div>
        </div>
        """, unsafe_allow_html=True)

heroes_col1, heroes_col2, heroes_col3, heroes_col4 = st.columns(4)

if not member_stats_df.empty and not logs_df.empty and 'name' in member_stats_df.columns:
    logs_with_names = pd.merge(logs_df, members_df[['members_id', 'name']], left_on='member_id', right_on='members_id', how='left')

    # 1. Mastermind (Points)
    hero_points = member_stats_df.loc[member_stats_df['total_points'].idxmax()]
    display_hero(heroes_col1, "🧠 العقل المدبّر", hero_points.get('name', 'N/A'), f"{int(hero_points.get('total_points', 0))} نقطة")

    # 2. Lord of the Hours (Total Reading Time)
    member_stats_df['total_reading_minutes'] = member_stats_df['total_reading_minutes_common'] + member_stats_df['total_reading_minutes_other']
    hero_hours = member_stats_df.loc[member_stats_df['total_reading_minutes'].idxmax()]
    display_hero(heroes_col2, "⏳ سيد الساعات", hero_hours.get('name', 'N/A'), f"{hero_hours.get('total_reading_minutes', 0) / 60:.1f} ساعة")

    # 3. Bookworm (Total Books)
    member_stats_df['total_books_read'] = member_stats_df['total_common_books_read'] + member_stats_df['total_other_books_read']
    hero_books = member_stats_df.loc[member_stats_df['total_books_read'].idxmax()]
    display_hero(heroes_col3, "📚 الديدان القارئ", hero_books.get('name', 'N/A'), f"{int(hero_books.get('total_books_read',0))} كتب")

    # 4. Pearl Hunter (Total Quotes)
    hero_quotes = member_stats_df.loc[member_stats_df['total_quotes_submitted'].idxmax()]
    display_hero(heroes_col4, "💎 صائد الدرر", hero_quotes.get('name', 'N/A'), f"{int(hero_quotes.get('total_quotes_submitted',0))} اقتباساً")

    # 5. The Long-Hauler (Consistency)
    consistency = logs_with_names.groupby('name')['submission_date_dt'].nunique().reset_index()
    if not consistency.empty:
        hero_consistency = consistency.loc[consistency['submission_date_dt'].idxmax()]
        display_hero(heroes_col1, "🏃‍♂️ صاحب النَفَس الطويل", hero_consistency.get('name', 'N/A'), f"{hero_consistency.get('submission_date_dt', 0)} يوم قراءة")
    else:
        display_hero(heroes_col1, "🏃‍♂️ صاحب النَفَس الطويل", "لا يوجد", "0 يوم")

    # 6. The Sprinter (Best Single Day)
    daily_sum = logs_with_names.groupby(['name', pd.Grouper(key='submission_date_dt', freq='D')])['total_minutes'].sum().reset_index()
    if not daily_sum.empty and daily_sum['total_minutes'].max() > 0:
        hero_daily = daily_sum.loc[daily_sum['total_minutes'].idxmax()]
        display_hero(heroes_col2, "⚡ العدّاء السريع", hero_daily['name'], f"{hero_daily['total_minutes'] / 60:.1f} ساعة في يوم")
    else:
        display_hero(heroes_col2, "⚡ العدّاء السريع", "لا يوجد", "0 ساعة في يوم")

    # 7. Star of the Week (Best Single Week)
    weekly_sum = logs_with_names.groupby(['name', pd.Grouper(key='submission_date_dt', freq='W-SAT')])['total_minutes'].sum().reset_index()
    if not weekly_sum.empty and weekly_sum['total_minutes'].max() > 0:
        hero_weekly = weekly_sum.loc[weekly_sum['total_minutes'].idxmax()]
        display_hero(heroes_col3, "⭐ نجم الأسبوع", hero_weekly['name'], f"{hero_weekly['total_minutes'] / 60:.1f} ساعة في أسبوع")
    else:
         display_hero(heroes_col3, "⭐ نجم الأسبوع", "لا يوجد", "0 ساعة في أسبوع")

    # 8. Giant of the Month (Best Single Month)
    monthly_sum = logs_with_names.groupby(['name', pd.Grouper(key='submission_date_dt', freq='M')])['total_minutes'].sum().reset_index()
    if not monthly_sum.empty and monthly_sum['total_minutes'].max() > 0:
        hero_monthly = monthly_sum.loc[monthly_sum['total_minutes'].idxmax()]
        display_hero(heroes_col4, "💪 عملاق الشهر", hero_monthly['name'], f"{hero_monthly['total_minutes'] / 60:.1f} ساعة في شهر")
    else:
        display_hero(heroes_col4, "💪 عملاق الشهر", "لا يوجد", "0 ساعة في شهر")
else:
    st.info("لا توجد بيانات كافية لعرض لوحة شرف الأبطال بعد.")
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

# --- Analytical Charts Section ---
st.subheader("📈 الرسوم البيانية التحليلية")
charts_col1, charts_col2 = st.columns(2, gap="large")

fig_growth, fig_rhythm = None, None

with charts_col1:
    st.markdown("##### نمو القراءة التراكمي")
    if not logs_df.empty:
        daily_minutes_growth = logs_df.groupby(logs_df['submission_date_dt'].dt.date)['total_minutes'].sum().reset_index(name='minutes')
        daily_minutes_growth = daily_minutes_growth.sort_values('submission_date_dt')
        daily_minutes_growth['cumulative_hours'] = daily_minutes_growth['minutes'].cumsum() / 60
        fig_growth = px.area(daily_minutes_growth, x='submission_date_dt', y='cumulative_hours', 
                             labels={'submission_date_dt': 'التاريخ', 'cumulative_hours': 'مجموع الساعات التراكمي'},
                             markers=False, color_discrete_sequence=['#2ECC71'])
        fig_growth.update_layout(title='', margin=dict(t=20, b=0, l=0, r=0), yaxis={'side': 'right'})
        st.plotly_chart(fig_growth, use_container_width=True)
    else:
        st.info("لا توجد بيانات لعرض المخطط.")

with charts_col2:
    st.markdown("##### إيقاع القراءة اليومي للفريق")
    if not logs_df.empty:
        daily_team_minutes = logs_df.groupby(logs_df['submission_date_dt'].dt.date)['total_minutes'].sum().reset_index()
        daily_team_minutes.rename(columns={'submission_date_dt': 'التاريخ', 'total_minutes': 'مجموع الدقائق'}, inplace=True)
        daily_team_minutes['مجموع الساعات'] = daily_team_minutes['مجموع الدقائق'] / 60
        
        fig_rhythm = px.line(daily_team_minutes, x='التاريخ', y='مجموع الساعات',
                             labels={'التاريخ': 'التاريخ', 'مجموع الساعات': 'مجموع الساعات المقروءة'},
                             markers=True, color_discrete_sequence=['#3498DB'])
        fig_rhythm.update_layout(
            title='', margin=dict(t=20, b=0, l=0, r=0), 
            yaxis={'side': 'right'},
            xaxis_title="", yaxis_title="الساعات"
        )
        st.plotly_chart(fig_rhythm, use_container_width=True)
    else:
        st.info("لا توجد بيانات لعرض المخطط.")
st.markdown("---")


# --- Leaderboards & Focus Section ---
st.subheader("🏆 قوائم المتصدرين وتركيز القراءة")
leader_col1, leader_col2, leader_col3 = st.columns([2, 1, 2], gap="large")

fig_points_leaderboard, fig_donut, fig_hours_leaderboard = None, None, None

with leader_col1:
    st.markdown("##### ⭐ المتصدرون بالنقاط")
    if not member_stats_df.empty and 'name' in member_stats_df.columns:
        points_leaderboard_df = member_stats_df.sort_values('total_points', ascending=False).head(10)[['name', 'total_points']].rename(columns={'name': 'الاسم', 'total_points': 'النقاط'})
        fig_points_leaderboard = px.bar(points_leaderboard_df, x='النقاط', y='الاسم', orientation='h', 
                                        text='النقاط', color_discrete_sequence=['#9b59b6'])
        fig_points_leaderboard.update_traces(textposition='outside')
        fig_points_leaderboard.update_layout(
            title='', 
            yaxis={'side': 'right', 'autorange': 'reversed'}, 
            xaxis_autorange='reversed', 
            margin=dict(t=20, b=0, l=0, r=0)
        )
        st.plotly_chart(fig_points_leaderboard, use_container_width=True)
    else:
        st.info("لا توجد بيانات.")

with leader_col2:
    st.markdown("##### 🎯 تركيز القراءة")
    if not member_stats_df.empty:
        total_common_minutes = member_stats_df['total_reading_minutes_common'].sum()
        total_other_minutes = member_stats_df['total_reading_minutes_other'].sum()
        if total_common_minutes > 0 or total_other_minutes > 0:
            donut_labels = ['الكتاب المشترك', 'الكتب الأخرى']
            donut_values = [total_common_minutes, total_other_minutes]
            colors = ['#3498db', '#f1c40f']
            fig_donut = go.Figure(data=[go.Pie(labels=donut_labels, values=donut_values, hole=.5, marker_colors=colors)])
            fig_donut.update_layout(showlegend=True, legend=dict(x=0.5, y=-0.2, xanchor='center', yanchor='bottom', orientation='h'), margin=dict(t=20, b=20, l=20, r=20), annotations=[dict(text='التوزيع', x=0.5, y=0.5, font_size=14, showarrow=False)])
            st.plotly_chart(fig_donut, use_container_width=True)
        else:
            st.info("لا توجد بيانات.")
    else:
        st.info("لا توجد بيانات.")

with leader_col3:
    st.markdown("##### ⏳ المتصدرون بالساعات")
    if not member_stats_df.empty and 'name' in member_stats_df.columns:
        member_stats_df['total_hours'] = (member_stats_df['total_reading_minutes_common'] + member_stats_df['total_reading_minutes_other']) / 60
        hours_leaderboard_df = member_stats_df.sort_values('total_hours', ascending=False).head(10)[['name', 'total_hours']].rename(columns={'name': 'الاسم', 'total_hours': 'الساعات'})
        hours_leaderboard_df['الساعات'] = hours_leaderboard_df['الساعات'].round(1)
        fig_hours_leaderboard = px.bar(hours_leaderboard_df, x='الساعات', y='الاسم', orientation='h', 
                                       text='الساعات', color_discrete_sequence=['#e67e22'])
        fig_hours_leaderboard.update_traces(texttemplate='%{text:.1f}', textposition='outside')
        fig_hours_leaderboard.update_layout(
            title='', 
            yaxis={'side': 'right', 'autorange': 'reversed'}, 
            xaxis_autorange='reversed', 
            margin=dict(t=20, b=0, l=0, r=0)
        )
        st.plotly_chart(fig_hours_leaderboard, use_container_width=True)
    else:
        st.info("لا توجد بيانات.")


# --- PDF Export Section ---
st.markdown("---")
with st.expander("🖨️ تصدير تقرير الأداء (PDF)"):
    st.info("اضغط على الزر أدناه لتصدير تقرير شامل للوحة التحكم العامة.")
    
    if st.button("🚀 إنشاء وتصدير تقرير لوحة التحكم", use_container_width=True, type="primary"):
        with st.spinner("جاري إنشاء التقرير..."):
            pdf = PDFReporter()
            
            champions_data = {}
            if not member_stats_df.empty and 'name' in member_stats_df.columns:
                king_of_reading = member_stats_df.loc[member_stats_df['total_reading_minutes'].idxmax()]
                king_of_points = member_stats_df.loc[member_stats_df['total_points'].idxmax()]
                king_of_books = member_stats_df.loc[member_stats_df['total_books_read'].idxmax()]
                king_of_quotes = member_stats_df.loc[member_stats_df['total_quotes_submitted'].idxmax()]
                champions_data["👑 ملك القراءة"] = king_of_reading.get('name', 'N/A')
                champions_data["⭐ ملك النقاط"] = king_of_points.get('name', 'N/A')
                champions_data["📚 ملك الكتب"] = king_of_books.get('name', 'N/A')
                champions_data["✍️ ملك الاقتباسات"] = king_of_quotes.get('name', 'N/A')

            kpis_main_pdf = {
                "⏳ إجمالي ساعات القراءة": total_hours_val,
                "📚 إجمالي الكتب المنهَاة": total_books_finished_val,
                "✍️ إجمالي الاقتباسات": total_quotes_val
            }
            kpis_secondary_pdf = {
                "👥 الأعضاء النشطون": active_members_count_val,
                "🏁 التحديات المكتملة": completed_challenges_count_val,
                "🗓️ أيام القراءة": total_reading_days_val
            }
            group_stats_for_pdf = {
                "total": len(members_df),
                "active": int(active_members_count_val) if active_members_count_val else 0,
                "inactive": len(members_df) - (int(active_members_count_val) if active_members_count_val else 0),
            }
            
            dashboard_data = {
                "kpis_main": kpis_main_pdf,
                "kpis_secondary": kpis_secondary_pdf,
                "champions_data": champions_data,
                "fig_growth": fig_growth, 
                "fig_donut": fig_donut,
                "fig_bar_days": None, # This chart was removed
                "fig_points_leaderboard": fig_points_leaderboard,
                "fig_hours_leaderboard": fig_hours_leaderboard,
                "group_stats": group_stats_for_pdf,
                "periods_df": periods_df
            }
            pdf.add_dashboard_report(dashboard_data)

            pdf_output = bytes(pdf.output())
            st.session_state.pdf_file = pdf_output
            st.toast("تم إنشاء ملف PDF بنجاح!", icon="📄")
            st.rerun()

    if 'pdf_file' in st.session_state:
        pdf_file = st.session_state.pdf_file
        st.download_button(
            label="📥 تحميل التقرير الآن",
            data=pdf_file,
            file_name=f"ReadingMarathon_Report_Dashboard_{date.today()}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
        if st.button("إغلاق"):
            del st.session_state.pdf_file
            st.rerun()