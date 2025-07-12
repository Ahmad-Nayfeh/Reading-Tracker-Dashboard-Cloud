import streamlit as st
import pandas as pd
from datetime import date, timedelta, datetime
import db_manager as db
import plotly.express as px
import plotly.graph_objects as go
from pdf_reporter import PDFReporter
import auth_manager
from utils import apply_chart_theme # <-- استيراد الدالة الجديدة
import style_manager  # <-- السطر الأول

style_manager.apply_sidebar_styles()  # <-- السطر الثاني

st.set_page_config(
    page_title="لوحة التحكم العامة",
    page_icon="📈",
    layout="wide"
)

# This CSS snippet enforces RTL layout and adds custom styles
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

        /* --- KPI Card Styles --- */
        .kpi-card {
            background-color: #ffffff;
            border-radius: 15px;
            padding: 20px;
            display: flex;
            align-items: center;
            border-left: 5px solid var(--kpi-color);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            transition: transform 0.2s;
            height: 120px;
            margin-bottom: 15px; /* Add margin for spacing */
        }
        .kpi-card:hover {
            transform: translateY(-4px);
        }
        .kpi-icon {
            font-size: 2.5em;
            padding: 0px 20px;
            color: var(--kpi-color);
        }
        .kpi-text {
            flex-grow: 1;
            text-align: right;
        }
        .kpi-value {
            font-size: 2.2em;
            font-weight: 700;
            color: #2c3e50;
        }
        .kpi-label {
            font-size: 1.1em;
            color: #5D6D7E;
        }
        
        /* Custom styles for the hero metric cards */
        .metric-card {
            background-color: #f9f9f9;
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            border: 1px solid #e6e6e6;
            margin-bottom: 10px;
            height: 130px; /* Fixed height for alignment */
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        .metric-card .label {
            font-size: 1.1em;
            font-weight: bold;
            color: #2980b9; /* Accent color for the title */
        }
        .metric-card .value {
            font-size: 1.5em;
            color: #2c3e50; /* Darker color for the name */
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .metric-card .sub-value {
            font-size: 1.0em;
            color: #7f8c8d; /* Gray for the number */
        }
        
        /* --- Professional News Ticker Styles --- */
        .news-container {
            background-color: #ffffff;
            border-radius: 12px;
            padding: 0;
            margin-bottom: 20px;
            border: 1px solid #e0e0e0;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            overflow: hidden; /* Important for rounded corners on children */
        }
        .news-header {
            background-color: #2980b9;
            color: white;
            padding: 12px 20px;
            font-size: 1.3em;
            font-weight: bold;
        }
        .news-body {
            padding: 15px 20px;
        }
        .news-body ul {
            list-style-type: none;
            padding-right: 0;
            margin: 0;
        }
        .news-body li {
            padding: 8px 0;
            border-bottom: 1px solid #f0f0f0;
            font-size: 1.1em;
            color: #34495e;
        }
        .news-body li:last-child {
            border-bottom: none;
        }
        .news-body li b {
            color: #2c3e50;
        }
        .news-body .no-news {
            color: #7f8c8d;
            font-style: italic;
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


# --- Logic for News Ticker ---
def get_heroes_at_date(target_date, logs_df, achievements_df, members_df):
    """Calculates all hero stats up to a specific date."""
    if logs_df.empty or members_df.empty:
        return {}

    # Filter data up to the target date
    logs_past = logs_df[logs_df['submission_date_dt'].dt.date <= target_date]
    achievements_past = achievements_df[achievements_df['achievement_date_dt'].dt.date <= target_date]

    if logs_past.empty:
        return {}

    # Calculate stats
    # 1. Total Points and Reading Minutes from logs
    member_stats = logs_past.groupby('member_id').agg(
        total_reading_minutes_common=('common_book_minutes', 'sum'),
        total_reading_minutes_other=('other_book_minutes', 'sum'),
        total_quotes_submitted=('total_quotes_submitted', 'sum')
    ).reset_index()

    # 2. Total books and meetings attended from achievements
    if not achievements_past.empty:
        ach_stats = achievements_past.groupby('member_id').agg(
            total_common_books_read=('achievement_type', lambda x: (x == 'FINISHED_COMMON_BOOK').sum()),
            total_other_books_read=('achievement_type', lambda x: (x == 'FINISHED_OTHER_BOOK').sum()),
        ).reset_index()
        member_stats = pd.merge(member_stats, ach_stats, on='member_id', how='left')
    else:
        member_stats['total_common_books_read'] = 0
        member_stats['total_other_books_read'] = 0
    
    # Fill NaN values after merge
    member_stats.fillna(0, inplace=True)
    member_stats['total_reading_minutes'] = member_stats['total_reading_minutes_common'] + member_stats['total_reading_minutes_other']
    member_stats['total_books_read'] = member_stats['total_common_books_read'] + member_stats['total_other_books_read']


    # Merge with member names
    member_stats = pd.merge(member_stats, members_df[['members_id', 'name']], left_on='member_id', right_on='members_id', how='left')
    
    # Calculate more complex stats
    # Consistency
    consistency = logs_past.groupby('name')['submission_date_dt'].nunique().reset_index()
    consistency.rename(columns={'submission_date_dt': 'days_read'}, inplace=True)
    member_stats = pd.merge(member_stats, consistency, on='name', how='left')

    # Best single day/week/month
    daily_sum = logs_past.groupby(['name', pd.Grouper(key='submission_date_dt', freq='D')])['total_minutes'].sum().reset_index()
    weekly_sum = logs_past.groupby(['name', pd.Grouper(key='submission_date_dt', freq='W-SAT')])['total_minutes'].sum().reset_index()
    monthly_sum = logs_past.groupby(['name', pd.Grouper(key='submission_date_dt', freq='M')])['total_minutes'].sum().reset_index()

    def get_max_for_member(df, value_col):
        if df.empty: return pd.Series()
        return df.groupby('name')[value_col].max()
        
    member_stats = pd.merge(member_stats, get_max_for_member(daily_sum, 'total_minutes').rename('max_daily'), on='name', how='left')
    member_stats = pd.merge(member_stats, get_max_for_member(weekly_sum, 'total_minutes').rename('max_weekly'), on='name', how='left')
    member_stats = pd.merge(member_stats, get_max_for_member(monthly_sum, 'total_minutes').rename('max_monthly'), on='name', how='left')

    member_stats.fillna(0, inplace=True)

    # Simplified points calculation for headlines - a more accurate one is in main.py
    # For this purpose, we can use a proxy or just focus on non-point metrics
    # Here, we'll just add a placeholder for total_points
    member_stats['total_points'] = member_stats['total_reading_minutes'] / 10 # Example proxy

    heroes = {}
    hero_metrics = {
        "🧠 العقل المدبّر": "total_points",
        "⏳ سيد الساعات": "total_reading_minutes",
        "📚 الديدان القارئ": "total_books_read",
        "💎 صائد الدرر": "total_quotes_submitted",
        "🏃‍♂️ صاحب النَفَس الطويل": "days_read",
        "⚡ العدّاء السريع": "max_daily",
        "⭐ نجم الأسبوع": "max_weekly",
        "💪 عملاق الشهر": "max_monthly",
    }
    
    for hero_title, metric_col in hero_metrics.items():
        if metric_col in member_stats.columns:
            max_value = member_stats[metric_col].max()
            if pd.notna(max_value) and max_value > 0:
                winners = member_stats[member_stats[metric_col] == max_value]['name'].tolist()
                heroes[hero_title] = sorted(winners)
            else:
                heroes[hero_title] = [] # No one has this title yet
    return heroes

def generate_headline_news(logs_df, achievements_df, members_df):
    today = date.today()
    last_week_date = today - timedelta(days=7)
    news_list = []

    # Ensure data is ready for processing
    if logs_df.empty or (today - logs_df['submission_date_dt'].min().date()).days < 7:
        news_list.append("أهلاً بكم في ماراثون القراءة! نتطلع لرؤية إنجازاتكم.")
        return news_list

    heroes_today = get_heroes_at_date(today, logs_df, achievements_df, members_df)
    heroes_last_week = get_heroes_at_date(last_week_date, logs_df, achievements_df, members_df)

    if not heroes_today or not heroes_last_week:
        news_list.append("جاري تحليل البيانات الأسبوعية...")
        return news_list
    
    # Compare heroes
    for title, current_winners in heroes_today.items():
        last_week_winners = heroes_last_week.get(title, [])
        
        # Convert lists to sets for easy comparison
        current_set = set(current_winners)
        last_week_set = set(last_week_winners)

        if not current_set:
            continue # No one has this title yet, so no news

        # Case 1: First ever winner(s) for this title
        if not last_week_set and current_set:
            names = " و ".join([f"<b>{name}</b>" for name in current_winners])
            news_list.append(f"🏆 <b>إنجاز غير مسبوق:</b> {names} أصبح أول من يحصل على لقب '{title}'!")
            continue

        # Case 2: Change in leadership
        if current_set != last_week_set:
            newly_joined = current_set - last_week_set
            if newly_joined:
                new_names = " و ".join([f"<b>{name}</b>" for name in list(newly_joined)])
                # Subcase 2a: Someone new joined an existing leader
                if last_week_set.issubset(current_set):
                     news_list.append(f"🤝 <b>منافسة على القمة:</b> {new_names} ينضم إلى الصدارة في لقب '{title}'!")
                # Subcase 2b: A completely new leader
                else:
                    news_list.append(f"🥇 <b>صعود جديد:</b> {new_names} يتصدر قائمة '{title}' هذا الأسبوع!")

    if not news_list:
        news_list.append("الأبطال يحافظون على مواقعهم! استمروا في العطاء هذا الأسبوع.")

    return news_list


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
    logs_df['total_quotes_submitted'] = logs_df['submitted_common_quote'] + logs_df['submitted_other_quote']


if not achievements_df.empty:
    achievements_df['achievement_date_dt'] = pd.to_datetime(achievements_df['achievement_date'], errors='coerce')
    
if not member_stats_df.empty and not members_df.empty:
    member_stats_df.rename(columns={'member_stats_id': 'members_id'}, inplace=True, errors='ignore')
    member_stats_df = pd.merge(member_stats_df, members_df[['members_id', 'name']], on='members_id', how='left')


# --- Page Rendering ---
st.header("📈 لوحة التحكم العامة")

# --- Dynamic Headline ---
st.markdown("---")
# Generate news items
news_items = generate_headline_news(logs_df.copy(), achievements_df.copy(), members_df.copy())

# Build the HTML string for the entire news ticker
news_html = '<div class="news-container">'
news_html += '<div class="news-header">📰 آخر أخبار الماراثون (آخر 7 أيام)</div>'
news_html += '<div class="news-body">'
if news_items:
    news_html += '<ul>'
    for item in news_items:
        news_html += f'<li>{item}</li>'
    news_html += '</ul>'
else:
    news_html += '<p class="no-news">لا توجد أخبار جديدة حالياً.</p>'
news_html += '</div></div>'

# Display the entire block with a single markdown command
st.markdown(news_html, unsafe_allow_html=True)
st.markdown("---")


# --- Main KPIs Section ---
st.subheader("📊 مؤشرات الأداء الرئيسية")

def display_main_kpi(col, label, value, icon, color):
    with col:
        st.markdown(f"""
        <div class="kpi-card" style="--kpi-color: {color};">
            <div class="kpi-icon">{icon}</div>
            <div class="kpi-text">
                <div class="kpi-value">{value}</div>
                <div class="kpi-label">{label}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# Calculate KPIs
total_hours_val = "0"
total_books_finished_val = "0"
total_quotes_val = "0"
active_members_count_val = "0"
total_reading_days_val = "0"
completed_challenges_count_val = "0"

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
    today_date_obj = date.today()
    periods_df['end_date_dt'] = pd.to_datetime(periods_df['end_date']).dt.date
    completed_challenges_count_val = f"{len(periods_df[periods_df['end_date_dt'] < today_date_obj])}"

# Display KPIs in two rows
kpi_row1_cols = st.columns(3)
display_main_kpi(kpi_row1_cols[0], "إجمالي ساعات القراءة", total_hours_val, "⏳", "#2980B9")
display_main_kpi(kpi_row1_cols[1], "إجمالي الكتب المنهَاة", total_books_finished_val, "📚", "#8E44AD")
display_main_kpi(kpi_row1_cols[2], "إجمالي الاقتباسات", total_quotes_val, "✍️", "#27AE60")

kpi_row2_cols = st.columns(3)
display_main_kpi(kpi_row2_cols[0], "الأعضاء النشطون", active_members_count_val, "👥", "#F39C12")
display_main_kpi(kpi_row2_cols[1], "إجمالي أيام القراءة", total_reading_days_val, "🗓️", "#E74C3C")
display_main_kpi(kpi_row2_cols[2], "التحديات المكتملة", completed_challenges_count_val, "🏁", "#16A085")

st.markdown("---")


# --- Hall of Fame Section ---
st.subheader("🌟 لوحة شرف الأبطال")

def display_hero(col, title, name, value_str):
    with col:
        st.markdown(f"""
        <div class="metric-card">
            <div class="label">{title}</div>
            <div class="value" title="{name}">{name}</div>
            <div class="sub-value">{value_str}</div>
        </div>
        """, unsafe_allow_html=True)

# Helper function to find winner(s)
def get_winners(df, column, name_col='name'):
    if df.empty or column not in df.columns:
        return "لا يوجد", 0
    
    max_value = df[column].max()
    
    if pd.isna(max_value) or max_value == 0:
        return "لا يوجد", 0
        
    winners_df = df[df[column] == max_value]
    winner_names = winners_df[name_col].tolist()
    
    return ", ".join(winner_names), max_value


heroes_col1, heroes_col2, heroes_col3, heroes_col4 = st.columns(4)

if not member_stats_df.empty and not logs_df.empty and 'name' in member_stats_df.columns:
    # Use the full stats calculated and stored in the database for the hall of fame
    # This ensures consistency with what the user sees elsewhere
    logs_with_names = pd.merge(logs_df, members_df[['members_id', 'name']], left_on='member_id', right_on='members_id', how='left')

    # 1. Mastermind (Points)
    winner_name, max_val = get_winners(member_stats_df, 'total_points')
    display_hero(heroes_col1, "🧠 العقل المدبّر", winner_name, f"{int(max_val)} نقطة")

    # 2. Lord of the Hours (Total Reading Time)
    member_stats_df['total_reading_minutes'] = member_stats_df['total_reading_minutes_common'] + member_stats_df['total_reading_minutes_other']
    winner_name, max_val = get_winners(member_stats_df, 'total_reading_minutes')
    display_hero(heroes_col2, "⏳ سيد الساعات", winner_name, f"{max_val / 60:.1f} ساعة")

    # 3. Bookworm (Total Books)
    member_stats_df['total_books_read'] = member_stats_df['total_common_books_read'] + member_stats_df['total_other_books_read']
    winner_name, max_val = get_winners(member_stats_df, 'total_books_read')
    display_hero(heroes_col3, "📚 الديدان القارئ", winner_name, f"{int(max_val)} كتب")

    # 4. Pearl Hunter (Total Quotes)
    winner_name, max_val = get_winners(member_stats_df, 'total_quotes_submitted')
    display_hero(heroes_col4, "💎 صائد الدرر", winner_name, f"{int(max_val)} اقتباساً")

    # 5. The Long-Hauler (Consistency)
    consistency = logs_with_names.groupby('name')['submission_date_dt'].nunique().reset_index()
    consistency.rename(columns={'submission_date_dt': 'days_read'}, inplace=True)
    winner_name, max_val = get_winners(consistency, 'days_read')
    display_hero(heroes_col1, "🏃‍♂️ صاحب النَفَس الطويل", winner_name, f"{int(max_val)} يوم قراءة")

    # 6. The Sprinter (Best Single Day)
    daily_sum = logs_with_names.groupby(['name', pd.Grouper(key='submission_date_dt', freq='D')])['total_minutes'].sum().reset_index()
    winner_name, max_val = get_winners(daily_sum, 'total_minutes')
    display_hero(heroes_col2, "⚡ العدّاء السريع", winner_name, f"{max_val / 60:.1f} ساعة في يوم")

    # 7. Star of the Week (Best Single Week)
    weekly_sum = logs_with_names.groupby(['name', pd.Grouper(key='submission_date_dt', freq='W-SAT')])['total_minutes'].sum().reset_index()
    winner_name, max_val = get_winners(weekly_sum, 'total_minutes')
    display_hero(heroes_col3, "⭐ نجم الأسبوع", winner_name, f"{max_val / 60:.1f} ساعة في أسبوع")

    # 8. Giant of the Month (Best Single Month)
    monthly_sum = logs_with_names.groupby(['name', pd.Grouper(key='submission_date_dt', freq='M')])['total_minutes'].sum().reset_index()
    winner_name, max_val = get_winners(monthly_sum, 'total_minutes')
    display_hero(heroes_col4, "💪 عملاق الشهر", winner_name, f"{max_val / 60:.1f} ساعة في شهر")
else:
    st.info("لا توجد بيانات كافية لعرض لوحة شرف الأبطال بعد.")
st.markdown("---")


# --- ############################################# ---
# --- ###      MODIFIED CHARTS SECTION START      ### ---
# --- ############################################# ---

st.subheader("📊 التحليلات الشاملة والمتصدرون")

# --- Initialize Figure Variables ---
fig_growth, fig_rhythm, fig_points_leaderboard, fig_donut, fig_hours_leaderboard, fig_weekly_activity = None, None, None, None, None, None

# --- NEW LOGIC TO EXTEND DATES ---
today_date_obj = pd.to_datetime(date.today())
full_date_range_df = pd.DataFrame()

if not logs_df.empty:
    min_date = logs_df['submission_date_dt'].min()
    if pd.notna(min_date):
        # Create a full date range from the first log entry to today
        all_days = pd.date_range(start=min_date, end=today_date_obj, freq='D')
        full_date_range_df = pd.DataFrame(all_days, columns=['submission_date_dt'])

# --- Calculate data for all charts first ---

# Growth Chart Data
if not logs_df.empty and not full_date_range_df.empty:
    daily_minutes_growth = logs_df.groupby(logs_df['submission_date_dt'])['total_minutes'].sum().reset_index(name='minutes')
    merged_growth = pd.merge(full_date_range_df, daily_minutes_growth, on='submission_date_dt', how='left').fillna(0)
    merged_growth['cumulative_hours'] = merged_growth['minutes'].cumsum() / 60
    fig_growth = px.area(merged_growth, x='submission_date_dt', y='cumulative_hours', 
                         labels={'submission_date_dt': 'التاريخ', 'cumulative_hours': 'مجموع الساعات التراكمي'})
    fig_growth = apply_chart_theme(fig_growth, 'area')
    fig_growth.update_layout(yaxis={'side': 'right'}, xaxis_autorange='reversed')

# Weekly Activity Chart Data
if not logs_df.empty:
    logs_df['weekday'] = logs_df['submission_date_dt'].dt.dayofweek
    weekday_map_ar = {
        0: 'الاثنين', 1: 'الثلاثاء', 2: 'الأربعاء', 3: 'الخميس', 
        4: 'الجمعة', 5: 'السبت', 6: 'الأحد'
    }
    logs_df['weekday_ar'] = logs_df['weekday'].map(weekday_map_ar)
    
    weekly_activity = logs_df.groupby('weekday_ar')['total_minutes'].sum().reset_index()
    total_minutes_all = weekly_activity['total_minutes'].sum()
    
    if total_minutes_all > 0:
        weekly_activity['percentage'] = (weekly_activity['total_minutes'] / total_minutes_all) * 100
        
        weekday_order_ar = ['السبت', 'الأحد', 'الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة']
        weekly_activity['weekday_ar'] = pd.Categorical(weekly_activity['weekday_ar'], categories=weekday_order_ar, ordered=True)
        weekly_activity = weekly_activity.sort_values('weekday_ar')

        fig_weekly_activity = px.bar(
            weekly_activity,
            x='weekday_ar',
            y='percentage',
            text=weekly_activity['percentage'].apply(lambda x: f'{x:.1f}%'),
            labels={'weekday_ar': 'يوم الأسبوع', 'percentage': 'نسبة النشاط (%)'},
            color_discrete_sequence=['#27AE60']
        )
        fig_weekly_activity = apply_chart_theme(fig_weekly_activity, 'bar')
        fig_weekly_activity.update_traces(textposition='outside')
        # CORRECTED: Added yaxis={'side': 'right'}
        fig_weekly_activity.update_layout(
            yaxis_title="النسبة المئوية للنشاط",
            yaxis={'side': 'right'}
        )


# Rhythm Chart Data
if not logs_df.empty and not full_date_range_df.empty:
    daily_team_minutes = logs_df.groupby(logs_df['submission_date_dt'])['total_minutes'].sum().reset_index()
    merged_team_minutes = pd.merge(full_date_range_df, daily_team_minutes, on='submission_date_dt', how='left').fillna(0)
    merged_team_minutes.rename(columns={'submission_date_dt': 'التاريخ', 'total_minutes': 'مجموع الدقائق'}, inplace=True)
    merged_team_minutes['مجموع الساعات'] = merged_team_minutes['مجموع الدقائق'] / 60
    fig_rhythm = px.line(merged_team_minutes, x='التاريخ', y='مجموع الساعات',
                         labels={'التاريخ': 'التاريخ', 'مجموع الساعات': 'مجموع الساعات المقروءة'},
                         markers=True)
    fig_rhythm = apply_chart_theme(fig_rhythm, 'line')
    fig_rhythm.update_layout(yaxis={'side': 'right'}, xaxis_autorange='reversed')

# Points Leaderboard Data
if not member_stats_df.empty and 'name' in member_stats_df.columns:
    points_leaderboard_df = member_stats_df.sort_values('total_points', ascending=False).head(10)[['name', 'total_points']].rename(columns={'name': 'الاسم', 'total_points': 'النقاط'})
    fig_points_leaderboard = px.bar(points_leaderboard_df, x='النقاط', y='الاسم', orientation='h', 
                                    text='النقاط', color_discrete_sequence=['#8E44AD'])
    fig_points_leaderboard = apply_chart_theme(fig_points_leaderboard, 'bar')
    fig_points_leaderboard.update_traces(textposition='outside')
    fig_points_leaderboard.update_layout(yaxis={'side': 'right', 'autorange': 'reversed'}, xaxis_autorange='reversed')

# Donut Chart Data
if not member_stats_df.empty:
    total_common_minutes = member_stats_df['total_reading_minutes_common'].sum()
    total_other_minutes = member_stats_df['total_reading_minutes_other'].sum()
    if total_common_minutes > 0 or total_other_minutes > 0:
        donut_labels = ['الكتاب المشترك', 'الكتب الأخرى']
        donut_values = [total_common_minutes, total_other_minutes]
        fig_donut = go.Figure(data=[go.Pie(labels=donut_labels, values=donut_values, hole=.6)])
        fig_donut = apply_chart_theme(fig_donut, 'pie')
        fig_donut.update_layout(
            showlegend=True, 
            legend=dict(x=0.5, y=-0.1, xanchor='center', yanchor='bottom', orientation='h'), 
            margin=dict(t=20, b=20, l=20, r=20), 
            annotations=[dict(text='التوزيع', x=0.5, y=0.5, font_size=16, showarrow=False)]
        )

# Hours Leaderboard Data
if not member_stats_df.empty and 'name' in member_stats_df.columns:
    member_stats_df['total_hours'] = (member_stats_df['total_reading_minutes_common'] + member_stats_df['total_reading_minutes_other']) / 60
    hours_leaderboard_df = member_stats_df.sort_values('total_hours', ascending=False).head(10)[['name', 'total_hours']].rename(columns={'name': 'الاسم', 'total_hours': 'الساعات'})
    hours_leaderboard_df['الساعات'] = hours_leaderboard_df['الساعات'].round(1)
    fig_hours_leaderboard = px.bar(hours_leaderboard_df, x='الساعات', y='الاسم', orientation='h', 
                                   text='الساعات', color_discrete_sequence=['#F39C12'])
    fig_hours_leaderboard = apply_chart_theme(fig_hours_leaderboard, 'bar')
    fig_hours_leaderboard.update_traces(texttemplate='%{text:.1f}', textposition='outside')
    fig_hours_leaderboard.update_layout(yaxis={'side': 'right', 'autorange': 'reversed'}, xaxis_autorange='reversed')


# --- Display all charts in a structured layout ---

# --- Row 1: Main Analytical Charts ---
# CORRECTED: Changed to 3 columns
row1_col1, row1_col2, row1_col3 = st.columns(3, gap="large") 
with row1_col1:
    st.markdown("##### نمو القراءة التراكمي")
    if fig_growth:
        st.plotly_chart(fig_growth, use_container_width=True)
    else:
        st.info("لا توجد بيانات لعرض المخطط.")

# CORRECTED: Added the new chart to the middle column
with row1_col2:
    st.markdown("##### نشاط القراءة الأسبوعي")
    if fig_weekly_activity:
        st.plotly_chart(fig_weekly_activity, use_container_width=True)
    else:
        st.info("لا توجد بيانات كافية لعرض نشاط الأسبوع.")

# CORRECTED: Moved the rhythm chart to the third column
with row1_col3:
    st.markdown("##### إيقاع القراءة اليومي للفريق")
    if fig_rhythm:
        st.plotly_chart(fig_rhythm, use_container_width=True)
    else:
        st.info("لا توجد بيانات لعرض المخطط.")


st.markdown("<br>", unsafe_allow_html=True) 

# --- Row 2: Leaderboards and Focus Chart ---
row2_col1, row2_col2, row2_col3 = st.columns([2, 1, 2], gap="large")
with row2_col1:
    st.markdown("##### ⭐ المتصدرون بالنقاط")
    if fig_points_leaderboard:
        st.plotly_chart(fig_points_leaderboard, use_container_width=True)
    else:
        st.info("لا توجد بيانات.")

with row2_col2:
    st.markdown("##### 🎯 تركيز القراءة")
    if fig_donut:
        st.plotly_chart(fig_donut, use_container_width=True)
    else:
        st.info("لا توجد بيانات.")

with row2_col3:
    st.markdown("##### ⏳ المتصدرون بالساعات")
    if fig_hours_leaderboard:
        st.plotly_chart(fig_hours_leaderboard, use_container_width=True)
    else:
        st.info("لا توجد بيانات.")

# --- ########################################### ---
# --- ###      MODIFIED CHARTS SECTION END      ### ---
# --- ########################################### ---


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
                "� إجمالي الكتب المنهَاة": total_books_finished_val,
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
            
            # Note: The new weekly activity chart is not added to the PDF report in this step.
            # That would be a separate task.
            dashboard_data = {
                "kpis_main": kpis_main_pdf,
                "kpis_secondary": kpis_secondary_pdf,
                "champions_data": champions_data,
                "fig_growth": fig_growth, 
                "fig_donut": fig_donut,
                "fig_bar_days": fig_weekly_activity, # Pass the new chart here if you want it in the PDF
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