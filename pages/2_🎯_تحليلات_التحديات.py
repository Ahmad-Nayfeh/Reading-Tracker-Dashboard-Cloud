import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
import db_manager as db
import chart_generator as charts
import plotly.graph_objects as go
from pdf_reporter import PDFReporter
import auth_manager
from utils import apply_chart_theme
import style_manager

style_manager.apply_sidebar_styles()

st.set_page_config(
    page_title="تحليلات التحديات",
    page_icon="🎯",
    layout="wide"
)


# This CSS snippet enforces RTL layout and adds custom styles
st.markdown("""
    <style>
        /* --- Base RTL and Font Fixes --- */
        .stApp { direction: rtl; }
        [data-testid="stSidebar"] { direction: rtl; }
        h1, h2, h3, h4, h5, h6, p, li, .st-bk, .st-b8, .st-b9, .st-ae { text-align: right !important; }
        .st-b8 label, .st-ae label { text-align: right !important; display: block; }
        
        /* --- Professional News Ticker Styles --- */
        .news-container {
            background-color: #ffffff; border-radius: 12px; padding: 0;
            margin-bottom: 20px; border: 1px solid #e0e0e0;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05); overflow: hidden;
        }
        .news-header { background-color: #2980b9; color: white; padding: 12px 20px; font-size: 1.3em; font-weight: bold; }
        .news-body { padding: 15px 20px; }
        .news-body ul { list-style-type: none; padding-right: 0; margin: 0; }
        .news-body li { padding: 8px 0; border-bottom: 1px solid #f0f0f0; font-size: 1.1em; color: #34495e; }
        .news-body li:last-child { border-bottom: none; }
        .news-body li b { color: #2c3e50; }
        .news-body .no-news { color: #7f8c8d; font-style: italic; }

        /* --- NEW: Glassmorphism Design for Challenge Summary --- */
        [data-testid="stAppViewContainer"] > .main {
            background-image: linear-gradient(120deg, #f0ecfc 0%, #c2e9fb 100%);
        }

        /* --- THE FIX: Target ONLY the top-level containers in our custom div --- */
        .summary-tab-content > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
            background: rgba(255, 255, 255, 0.25);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.18);
            padding: 25px;
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.1);
            color: #1E2A78;
            margin-top: 20px;
        }

        .card-title {
            font-weight: 700;
            font-size: 1.8em;
            color: #1E2A78;
            padding-bottom: 10px;
            border-bottom: 2px solid rgba(255, 255, 255, 0.5);
            margin-bottom: 20px;
        }

        .kpi-metric {
            text-align: center;
            padding: 15px;
            background: rgba(255, 255, 255, 0.3);
            border-radius: 15px;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        
        .kpi-metric .icon { font-size: 2.5em; }
        .kpi-metric .label { font-size: 1em; font-weight: 600; margin-top: 5px; }
        .kpi-metric .value { font-size: 2.5em; font-weight: 700; line-height: 1.2; }
        .kpi-metric .unit { font-size: 0.9em; }

        /* --- Reader Profile Card Styles (Applied to its own container) --- */
        .reader-kpi-box {
            background-color: #ffffff; border-radius: 12px; padding: 20px; text-align: center;
            border: 1px solid #e9ecef; transition: all 0.3s ease-in-out;
        }
        .reader-kpi-box:hover { transform: translateY(-5px); box-shadow: 0 6px 12px rgba(0,0,0,0.08); }
        .reader-kpi-box .icon { font-size: 2.5em; margin-bottom: 10px; }
        .reader-kpi-box .label { font-size: 1.1em; font-weight: 600; color: #6c757d; }
        .reader-kpi-box .value { font-size: 2em; font-weight: 700; color: #343a40; }
        .card-subheader {
            font-size: 1.5em; font-weight: 700; color: #34495e;
            margin-top: 25px; margin-bottom: 15px; padding-bottom: 10px;
            border-bottom: 3px solid #3498db; display: inline-block;
        }
        .badge-container {
            display: flex; align-items: center; background-color: #eafaf1;
            border-right: 5px solid #2ecc71; border-radius: 8px;
            padding: 15px; margin-bottom: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.04);
        }
        .badge-icon { font-size: 1.8em; margin-left: 15px; color: #2ecc71; }
        .badge-text { font-size: 1.1em; color: #2c3e50; }
        .achievement-item { font-size: 1.1em; padding: 8px 0; color: #34495e; }
        .achievement-item::before { content: "🎯"; margin-left: 10px; }

    </style>
""", unsafe_allow_html=True)


# --- 1. UNIFIED AUTHENTICATION BLOCK ---
creds = auth_manager.authenticate()
user_id = st.session_state.get('user_id')

if not creds or not user_id:
    st.error("مصادقة المستخدم مطلوبة. يرجى العودة إلى الصفحة الرئيسية وتسجيل الدخول.")
    st.stop()
# -----------------------------------------


# --- Helper Functions ---

def create_activity_heatmap(df, start_date, end_date, title_text=''):
    df = df.copy()
    if df.empty:
        fig = go.Figure()
        fig.update_layout(title="لا توجد بيانات قراءة لعرضها في الخريطة")
        return apply_chart_theme(fig)

    df['date'] = pd.to_datetime(df['submission_date_dt'])
    
    full_date_range = pd.to_datetime(pd.date_range(start=start_date, end=end_date, freq='D'))
    
    daily_minutes = df.groupby(df['date'].dt.date)['total_minutes'].sum()
    
    heatmap_data = pd.DataFrame({'date': daily_minutes.index, 'minutes': daily_minutes.values})
    heatmap_data['date'] = pd.to_datetime(heatmap_data['date'])
    
    heatmap_data = pd.merge(pd.DataFrame({'date': full_date_range}), heatmap_data, on='date', how='left').fillna(0)

    heatmap_data.loc[:, 'weekday_name'] = heatmap_data['date'].dt.strftime('%A')
    weekday_map_ar = {"Saturday": "السبت", "Sunday": "الأحد", "Monday": "الاثنين", "Tuesday": "الثلاثاء", "Wednesday": "الأربعاء", "Thursday": "الخميس", "Friday": "الجمعة"}
    heatmap_data.loc[:, 'weekday_ar'] = heatmap_data['weekday_name'].map(weekday_map_ar)
    
    heatmap_data['week_of_year'] = heatmap_data['date'].dt.isocalendar().week
    heatmap_data['month_abbr'] = heatmap_data['date'].dt.strftime('%b')
    heatmap_data['hover_text'] = heatmap_data.apply(lambda row: f"<b>{row['date'].strftime('%Y-%m-%d')} ({row['weekday_ar']})</b><br>دقائق القراءة: {int(row['minutes'])}", axis=1)

    weekday_order_ar = ["الأحد", "الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت"]
    heatmap_data['weekday_ar'] = pd.Categorical(heatmap_data['weekday_ar'], categories=weekday_order_ar, ordered=True)
    
    heatmap_pivot = heatmap_data.pivot_table(index='weekday_ar', columns='week_of_year', values='minutes', aggfunc='sum', observed=False).fillna(0)
    hover_pivot = heatmap_data.pivot_table(index='weekday_ar', columns='week_of_year', values='hover_text', aggfunc=lambda x: ' '.join(x), observed=False)
    
    heatmap_pivot = heatmap_pivot[sorted(heatmap_pivot.columns, reverse=True)]
    hover_pivot = hover_pivot[sorted(hover_pivot.columns, reverse=True)]

    month_positions = heatmap_data.drop_duplicates('month_abbr').set_index('month_abbr')
    
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_pivot,
        x=heatmap_pivot.columns,
        y=heatmap_pivot.index,
        colorscale='Greens',
        hoverongaps=False,
        customdata=hover_pivot,
        hovertemplate='%{customdata}<extra></extra>',
        colorbar=dict(x=-0.15, y=0.5, yanchor='middle', thickness=15)
    ))

    fig = apply_chart_theme(fig) # Apply the base theme
    
    fig.update_layout(
        title=title_text,
        xaxis_title='أسابيع التحدي',
        yaxis_title='',
        xaxis_autorange='reversed',
        yaxis={'side': 'right'},
        xaxis=dict(tickmode='array', tickvals=list(month_positions.week_of_year), ticktext=list(month_positions.index)),
        font_color='#1E2A78', # Override font color for this specific design
        margin=dict(l=80)
    )
    return fig

def generate_challenge_news(period_achievements_df, members_df, start_date_obj, end_date_obj, book_title):
    news_list = []
    today = date.today()

    # Case 1: Challenge hasn't started yet
    if today < start_date_obj:
        news_list.append(f"⏳ <b>الاستعدادات جارية:</b> سينطلق تحدي '{book_title}' في تاريخ {start_date_obj.strftime('%Y-%m-%d')}.")
        return news_list

    # Ensure members_df is not empty and has the required column
    if members_df.empty or 'members_id' not in members_df.columns:
        return ["لا يمكن عرض الأخبار، بيانات الأعضاء غير متوفرة."]

    finishers_df = period_achievements_df[period_achievements_df['achievement_type'] == 'FINISHED_COMMON_BOOK'].copy()
    
    if not finishers_df.empty:
        finishers_df = pd.merge(finishers_df, members_df[['members_id', 'name']], left_on='member_id', right_on='members_id', how='left')
        finishers_df.sort_values(by='achievement_date_dt', inplace=True)
    
    total_finishers = len(finishers_df)

    # Case 2: Challenge is active or finished, but no one has finished the book yet
    if finishers_df.empty:
        news_list.append(f"🏃‍♂️ <b>السباق محتدم:</b> لا يزال الجميع يتنافس لإنهاء كتاب '{book_title}'. من سيكون أول المنجزين؟")
    else:
        # Find the latest achievement day
        latest_achievement_date = finishers_df['achievement_date_dt'].max().date()
        finishers_on_latest_day = finishers_df[finishers_df['achievement_date_dt'].dt.date == latest_achievement_date]
        
        names_on_latest_day = [f"<b>{name}</b>" for name in finishers_on_latest_day['name']]
        
        # Craft the news for the latest achievement
        if len(names_on_latest_day) > 1:
            news_list.append(f"🎉 <b>إنجاز جماعي:</b> { ' و '.join(names_on_latest_day)} أنهوا الكتاب معًا في يوم {latest_achievement_date.strftime('%Y-%m-%d')}.")
        else:
            first_ever_finisher = finishers_df.iloc[0]
            if first_ever_finisher['member_id'] == finishers_on_latest_day.iloc[0]['member_id']:
                 news_list.append(f"🏁 <b>شرارة الإنجاز الأولى:</b> {names_on_latest_day[0]} هو أول من عبر خط النهاية وأنهى الكتاب!")
            else:
                news_list.append(f"👍 <b>ويستمر السباق:</b> {names_on_latest_day[0]} ينضم إلى قائمة المنجزين.")

        # Add a summary news item
        if total_finishers == 1:
            news_list.append("بطل واحد فقط وصل إلى خط النهاية حتى الآن.")
        else:
            news_list.append(f"<b>ملخص:</b> {total_finishers} أبطال أتموا قراءة الكتاب بنجاح حتى الآن.")

    # Case 3: Challenge has finished, check for discussion attendees
    if today > end_date_obj:
        attendees_df = period_achievements_df[period_achievements_df['achievement_type'] == 'ATTENDED_DISCUSSION'].copy()
        if not attendees_df.empty:
            attendees_df = pd.merge(attendees_df, members_df[['members_id', 'name']], left_on='member_id', right_on='members_id', how='left')
            attendee_names = [f"<b>{name}</b>" for name in attendees_df['name']]
            news_list.append(f"🗣️ <b>جلسة نقاش مثمرة:</b> نُشيد بحضور { ' و '.join(attendee_names)} للجلسة الختامية.")
        else:
            news_list.append("ℹ️ <b>ملاحظة:</b> لم يتم تسجيل حضور لأي عضو في جلسة النقاش الختامية.")
            
    return news_list


# --- Data Loading ---
@st.cache_data(ttl=300)
def load_all_data(user_id):
    all_data = db.get_all_data_for_stats(user_id)
    members_df = pd.DataFrame(all_data.get('members', []))
    periods_df = pd.DataFrame(all_data.get('periods', []))
    logs_df = pd.DataFrame(all_data.get('logs', []))
    achievements_df = pd.DataFrame(all_data.get('achievements', []))
    # NEW: Load the overall member stats
    member_stats_df = db.get_subcollection_as_df(user_id, 'member_stats')
    if not member_stats_df.empty and not members_df.empty:
        member_stats_df.rename(columns={'member_stats_id': 'members_id'}, inplace=True, errors='ignore')
        member_stats_df = pd.merge(member_stats_df, members_df[['members_id', 'name']], on='members_id', how='left')

    return members_df, periods_df, logs_df, achievements_df, member_stats_df

members_df, periods_df, logs_df, achievements_df, member_stats_df = load_all_data(user_id)

# --- Data Processing ---
if not logs_df.empty:
    logs_df['submission_date_dt'] = pd.to_datetime(logs_df['submission_date'], format='%d/%m/%Y', errors='coerce')
    logs_df['total_minutes'] = logs_df['common_book_minutes'] + logs_df['other_book_minutes']

if not achievements_df.empty:
    achievements_df['achievement_date_dt'] = pd.to_datetime(achievements_df['achievement_date'], errors='coerce')

# --- Page Rendering ---
st.header("🎯 تحليلات التحديات")

if periods_df.empty:
    st.info("لا توجد تحديات حالية أو سابقة لعرض تحليلاتها. يمكنك إضافة تحدي جديد من صفحة 'الإدارة والإعدادات'.")
    st.stop()

today = date.today()
challenge_options_map = {period['periods_id']: period for index, period in periods_df.iterrows()}
active_challenges, past_challenges, future_challenges = [], [], []

for period_id, period_data in challenge_options_map.items():
    start_date_obj = datetime.strptime(period_data['start_date'], '%Y-%m-%d').date()
    end_date_obj = datetime.strptime(period_data['end_date'], '%Y-%m-%d').date()
    if start_date_obj > today: future_challenges.append(period_id)
    elif end_date_obj < today: past_challenges.append(period_id)
    else: active_challenges.append(period_id)
        
future_challenges.sort(key=lambda pid: datetime.strptime(challenge_options_map[pid]['start_date'], '%Y-%m-%d').date())
past_challenges.sort(key=lambda pid: datetime.strptime(challenge_options_map[pid]['start_date'], '%Y-%m-%d').date(), reverse=True)
sorted_option_ids = future_challenges + active_challenges + past_challenges

if not sorted_option_ids:
    st.info("لا توجد تحديات لعرضها في الفلتر.")
    st.stop()

def format_challenge_option(period_id):
    period_data = challenge_options_map[period_id]
    status_emoji = ""
    if period_id in active_challenges: status_emoji = " (الحالي) 🟢"
    if period_id in past_challenges: status_emoji = " (السابق) 🏁"
    if period_id in future_challenges: status_emoji = " (المقبل) ⏳"
    return f"{period_data.get('book_title', 'تحدي غير معروف')} | {period_data['start_date']} إلى {period_data['end_date']}{status_emoji}"

default_index = 0
if active_challenges:
    active_id = active_challenges[0]
    if active_id in sorted_option_ids:
        default_index = sorted_option_ids.index(active_id)

selected_period_id = st.selectbox(
    "اختر تحدياً لعرض تحليلاته:",
    options=sorted_option_ids,
    format_func=format_challenge_option,
    index=default_index,
    key="challenge_selector"
)
st.markdown("---")

if selected_period_id:
    selected_challenge_data = challenge_options_map[selected_period_id]
    book_title = selected_challenge_data.get('book_title', 'N/A')
    st.subheader(f"تحليلات تحدي: {book_title}")

    start_date_obj = datetime.strptime(selected_challenge_data['start_date'], '%Y-%m-%d').date()
    end_date_obj = datetime.strptime(selected_challenge_data['end_date'], '%Y-%m-%d').date()
    
    period_logs_df = pd.DataFrame()
    if not logs_df.empty:
        period_logs_df = logs_df[(logs_df['submission_date_dt'].notna()) & (logs_df['submission_date_dt'].dt.date >= start_date_obj) & (logs_df['submission_date_dt'].dt.date <= end_date_obj)].copy()
    
    period_achievements_df = pd.DataFrame()
    if not achievements_df.empty:
        period_achievements_df = achievements_df[achievements_df['period_id'] == selected_period_id].copy()

    podium_df = pd.DataFrame()
    all_participants_names = []
    if not period_logs_df.empty:
        period_participants_ids = period_logs_df['member_id'].unique()
        period_members_df = members_df[members_df['members_id'].isin(period_participants_ids)]
        all_participants_names = period_members_df['name'].tolist()

        podium_data = []
        period_rules = selected_challenge_data

        for _, member in period_members_df.iterrows():
            member_id = member['member_id']
            member_logs = period_logs_df[period_logs_df['member_id'] == member_id]
            member_achievements = pd.DataFrame()
            if not period_achievements_df.empty:
                member_achievements = period_achievements_df[period_achievements_df['member_id'] == member_id]

            points = 0
            common_minutes, other_minutes, common_quotes, other_quotes = 0, 0, 0, 0
            if not member_logs.empty:
                common_minutes = member_logs['common_book_minutes'].sum()
                other_minutes = member_logs['other_book_minutes'].sum()
                common_quotes = member_logs['submitted_common_quote'].sum()
                other_quotes = member_logs['submitted_other_quote'].sum()

                if period_rules.get('minutes_per_point_common', 0) > 0: points += common_minutes // period_rules['minutes_per_point_common']
                if period_rules.get('minutes_per_point_other', 0) > 0: points += other_minutes // period_rules['minutes_per_point_other']
                points += common_quotes * period_rules.get('quote_common_book_points', 0)
                points += other_quotes * period_rules.get('quote_other_book_points', 0)
            
            if not member_achievements.empty:
                for _, ach in member_achievements.iterrows():
                    ach_type = ach['achievement_type']
                    if ach_type == 'FINISHED_COMMON_BOOK': points += period_rules.get('finish_common_book_points', 0)
                    elif ach_type == 'ATTENDED_DISCUSSION': points += period_rules.get('attend_discussion_points', 0)
                    elif ach_type == 'FINISHED_OTHER_BOOK': points += period_rules.get('finish_other_book_points', 0)

            podium_data.append({
                'member_id': member_id, 
                'name': member['name'], 
                'total_points': int(points), 
                'total_reading_minutes_common': common_minutes,
                'total_reading_minutes_other': other_minutes,
                'total_quotes_submitted': common_quotes + other_quotes
            })
        podium_df = pd.DataFrame(podium_data)

    finishers_names, attendees_names = [], []

    tab1, tab2 = st.tabs(["📝 ملخص التحدي", "🧑‍💻 بطاقة القارئ"])

    with tab1:
        st.markdown('<div class="summary-tab-content">', unsafe_allow_html=True)
        
        news_items = generate_challenge_news(period_achievements_df, members_df, start_date_obj, end_date_obj, book_title)
        news_html = '<div class="news-container">'
        news_html += f'<div class="news-header">🎯 آخر أخبار تحدي "{book_title}"</div>'
        news_html += '<div class="news-body">'
        if news_items:
            news_html += '<ul>'
            for item in news_items:
                news_html += f'<li>{item}</li>'
            news_html += '</ul>'
        else:
            news_html += '<p class="no-news">لا توجد أخبار جديدة حالياً لهذا التحدي.</p>'
        news_html += '</div></div>'
        st.markdown(news_html, unsafe_allow_html=True)

        if period_logs_df.empty and today >= start_date_obj:
            st.info("لا توجد بيانات مسجلة لهذا التحدي بعد.")
        elif today < start_date_obj:
            st.info(f"هذا التحدي لم يبدأ بعد. موعد الانطلاق: {start_date_obj.strftime('%Y-%m-%d')}")
        else:
            with st.container(border=True):
                st.markdown('<p class="card-title">لوحة المؤشرات العامة</p>', unsafe_allow_html=True)
                c1, c2, c3 = st.columns(3)
                
                with c1:
                    total_days = (end_date_obj - start_date_obj).days if end_date_obj > start_date_obj else 1
                    days_passed = (today - start_date_obj).days if today >= start_date_obj else 0
                    progress = min(1.0, days_passed / total_days if total_days > 0 else 0) * 100
                    
                    fig_gauge = go.Figure(go.Indicator(
                        mode="gauge+number", value=progress, number={'suffix': '%', 'font': {'color': "#1E2A78"}},
                        title={'text': f"انقضى {days_passed} من {total_days} يوم", 'font': {'size': 16, 'color': '#1E2A78'}},
                        gauge={'axis': {'range': [None, 100]}, 'bar': {'color': '#2980B9'}}))
                    fig_gauge.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20), paper_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_gauge, use_container_width=True)

                total_period_minutes = period_logs_df['total_minutes'].sum()
                total_period_hours = int(total_period_minutes // 60)
                active_participants = period_logs_df['member_id'].nunique()
                avg_daily_reading = (total_period_minutes / days_passed / active_participants) if days_passed > 0 and active_participants > 0 else 0
                total_period_quotes = period_logs_df['submitted_common_quote'].sum() + period_logs_df['submitted_other_quote'].sum()

                with c2:
                    st.markdown(f"""
                    <div class="kpi-metric">
                        <div class="icon">⏳</div>
                        <div class="label">مجموع ساعات القراءة</div>
                        <div class="value">{total_period_hours:,}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown(f"""
                    <div class="kpi-metric" style="margin-top: 15px;">
                        <div class="icon">✍️</div>
                        <div class="label">الاقتباسات المرسلة</div>
                        <div class="value">{int(total_period_quotes)}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with c3:
                    st.markdown(f"""
                    <div class="kpi-metric">
                        <div class="icon">👥</div>
                        <div class="label">المشاركون الفعليون</div>
                        <div class="value">{active_participants}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown(f"""
                    <div class="kpi-metric" style="margin-top: 15px;">
                        <div class="icon">📊</div>
                        <div class="label">متوسط القراءة/عضو</div>
                        <div class="value">{avg_daily_reading:.1f}</div>
                        <div class="unit">دقيقة/يوم</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            with st.container(border=True):
                st.markdown('<p class="card-title">التحليلات البيانية للتحدي</p>', unsafe_allow_html=True)

                chart_end_date = min(date.today(), end_date_obj)
                challenge_date_range_df = pd.DataFrame(
                    pd.date_range(start=start_date_obj, end=chart_end_date, freq='D'),
                    columns=['submission_date_dt']
                )

                fig_growth = charts.create_growth_chart(period_logs_df, challenge_date_range_df)
                fig_weekly_activity = charts.create_weekly_activity_chart(period_logs_df)
                fig_rhythm = charts.create_rhythm_chart(period_logs_df, challenge_date_range_df)
                fig_points_leaderboard = charts.create_points_leaderboard(podium_df)
                fig_hours_leaderboard = charts.create_hours_leaderboard(podium_df)
                fig_donut = charts.create_focus_donut(podium_df, 'total_reading_minutes_common', 'total_reading_minutes_other')

                st.markdown('<div style="color: #1E2A78;">', unsafe_allow_html=True)
                
                row1_col1, row1_col2, row1_col3 = st.columns(3, gap="large") 
                with row1_col1:
                    st.markdown("<h6>نمو القراءة التراكمي</h6>", unsafe_allow_html=True)
                    if fig_growth: st.plotly_chart(fig_growth, use_container_width=True)
                    else: st.info("لا توجد بيانات.")

                with row1_col2:
                    st.markdown("<h6>نشاط القراءة الأسبوعي</h6>", unsafe_allow_html=True)
                    if fig_weekly_activity: st.plotly_chart(fig_weekly_activity, use_container_width=True)
                    else: st.info("لا توجد بيانات.")

                with row1_col3:
                    st.markdown("<h6>إيقاع القراءة اليومي</h6>", unsafe_allow_html=True)
                    if fig_rhythm: st.plotly_chart(fig_rhythm, use_container_width=True)
                    else: st.info("لا توجد بيانات.")

                st.markdown("<br>", unsafe_allow_html=True) 

                row2_col1, row2_col2, row2_col3 = st.columns([2, 1, 2], gap="large")
                with row2_col1:
                    st.markdown("<h6>⭐ المتصدرون بالنقاط</h6>", unsafe_allow_html=True)
                    if fig_points_leaderboard: st.plotly_chart(fig_points_leaderboard, use_container_width=True)
                    else: st.info("لا توجد بيانات.")

                with row2_col2:
                    st.markdown("<h6>🎯 تركيز القراءة</h6>", unsafe_allow_html=True)
                    if fig_donut: st.plotly_chart(fig_donut, use_container_width=True)
                    else: st.info("لا توجد بيانات.")

                with row2_col3:
                    st.markdown("<h6>⏳ المتصدرون بالساعات</h6>", unsafe_allow_html=True)
                    if fig_hours_leaderboard: st.plotly_chart(fig_hours_leaderboard, use_container_width=True)
                    else: st.info("لا توجد بيانات.")
                
                st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        if member_stats_df.empty:
            st.info("لا يوجد مشاركون لعرض بطاقاتهم.")
        else:
            member_names = sorted(member_stats_df['name'].unique().tolist())
            selected_member_name = st.selectbox("اختر قارئاً لعرض بطاقته:", member_names)
            
            if selected_member_name:
                with st.container(border=True):
                    # --- Data Filtering for the selected reader (ALL TIME) ---
                    member_info = member_stats_df[member_stats_df['name'] == selected_member_name].iloc[0]
                    member_id = member_info['members_id']
                    
                    member_logs_all_time = logs_df[logs_df['member_id'] == member_id]
                    member_achievements_all_time = achievements_df[achievements_df['member_id'] == member_id]

                    # --- KPIs for the selected reader ---
                    kpi_cols = st.columns(3)
                    total_hours = (member_info['total_reading_minutes_common'] + member_info['total_reading_minutes_other']) / 60
                    with kpi_cols[0]:
                        st.markdown(f"""
                        <div class="reader-kpi-box">
                            <div class="icon">⭐</div>
                            <div class="label">إجمالي النقاط</div>
                            <div class="value">{int(member_info['total_points'])}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with kpi_cols[1]:
                        st.markdown(f"""
                        <div class="reader-kpi-box">
                            <div class="icon">⏳</div>
                            <div class="label">إجمالي الساعات</div>
                            <div class="value">{total_hours:.1f}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with kpi_cols[2]:
                        st.markdown(f"""
                        <div class="reader-kpi-box">
                            <div class="icon">✍️</div>
                            <div class="label">إجمالي الاقتباسات</div>
                            <div class="value">{int(member_info['total_quotes_submitted'])}</div>
                        </div>
                        """, unsafe_allow_html=True)

                    st.markdown("---")
                    
                    # --- Badges and Points Source Donut ---
                    col1, col2 = st.columns(2, gap="large")
                    
                    with col1:
                        st.markdown('<div class="card-subheader">🏅 الأوسمة والشارات</div>', unsafe_allow_html=True)
                        badges_unlocked = []
                        if member_info['total_quotes_submitted'] > 10: 
                            badges_unlocked.append(('✍️', 'وسام الفيلسوف: إرسال أكثر من 10 اقتباسات.'))
                        
                        if not member_achievements_all_time.empty:
                            finish_common_ach = member_achievements_all_time[member_achievements_all_time['achievement_type'] == 'FINISHED_COMMON_BOOK']
                            for _, ach in finish_common_ach.iterrows():
                                period_id = ach['period_id']
                                if period_id in challenge_options_map:
                                    period_start_date = datetime.strptime(challenge_options_map[period_id]['start_date'], '%Y-%m-%d').date()
                                    if (ach['achievement_date_dt'].date() - period_start_date).days <= 7:
                                        badges_unlocked.append(('🏃‍♂️', 'وسام العدّاء: إنهاء كتاب في الأسبوع الأول.'))
                                        break 
                        
                        if not member_logs_all_time.empty:
                            log_dates = sorted(pd.to_datetime(member_logs_all_time['submission_date_dt'].unique()))
                            if len(log_dates) >= 7:
                                max_streak, current_streak = 0, 0
                                if log_dates:
                                    current_streak = 1; max_streak = 1
                                    for i in range(1, len(log_dates)):
                                        if (log_dates[i] - log_dates[i-1]).days == 1: current_streak += 1
                                        else: max_streak = max(max_streak, current_streak); current_streak = 1
                                    max_streak = max(max_streak, current_streak)
                                if max_streak >= 7: 
                                    badges_unlocked.append(('💯', f'وسام المثابرة: القراءة لـ {max_streak} أيام متتالية.'))
                        
                        if badges_unlocked:
                            for icon, text in badges_unlocked:
                                st.markdown(f'<div class="badge-container"><div class="badge-icon">{icon}</div><div class="badge-text">{text}</div></div>', unsafe_allow_html=True)
                        else: 
                            st.info("لا توجد أوسمة بعد. استمر في القراءة لفتحها!")

                    with col2:
                        st.markdown('<div class="card-subheader">📊 مصادر النقاط</div>', unsafe_allow_html=True)
                        points_source_data = {}
                        # This part needs the full rules for all periods, which is complex.
                        # For simplicity, we'll approximate based on the main stats.
                        # A more accurate way would be to re-calculate from scratch, which is computationally expensive here.
                        points_source_data['قراءة الكتب'] = (member_info['total_reading_minutes_common'] // 10) + (member_info['total_reading_minutes_other'] // 5) # Approximation
                        points_source_data['إنهاء الكتب'] = (member_info['total_common_books_read'] * 50) + (member_info['total_other_books_read'] * 25) # Approximation
                        points_source_data['الاقتباسات'] = member_info['total_quotes_submitted'] * 2 # Approximation
                        points_source_data['حضور النقاش'] = member_info.get('meetings_attended', 0) * 25 # Approximation
                        
                        fig_points_source = charts.create_points_source_donut(points_source_data)
                        if fig_points_source:
                            st.plotly_chart(fig_points_source, use_container_width=True)
                        else:
                            st.info("لا توجد نقاط مسجلة لعرض مصادرها.")
                    
                    st.markdown("---")

                    # --- NEW: Unified Charts Section for the Reader ---
                    st.markdown('<div class="card-subheader">التحليلات البيانية لأداء القارئ</div>', unsafe_allow_html=True)
                    
                    if not member_logs_all_time.empty:
                        min_date_reader = member_logs_all_time['submission_date_dt'].min()
                        reader_date_range_df = pd.DataFrame(
                            pd.date_range(start=min_date_reader, end=date.today(), freq='D'),
                            columns=['submission_date_dt']
                        )
                        
                        fig_growth_reader = charts.create_growth_chart(member_logs_all_time, reader_date_range_df)
                        fig_weekly_activity_reader = charts.create_weekly_activity_chart(member_logs_all_time)
                        fig_rhythm_reader = charts.create_rhythm_chart(member_logs_all_time, reader_date_range_df)

                        r_col1, r_col2, r_col3 = st.columns(3, gap="large")
                        with r_col1:
                            st.markdown("<h6>نمو القراءة التراكمي</h6>", unsafe_allow_html=True)
                            if fig_growth_reader: st.plotly_chart(fig_growth_reader, use_container_width=True)
                            else: st.info("لا توجد بيانات.")
                        with r_col2:
                            st.markdown("<h6>نشاط القراءة الأسبوعي</h6>", unsafe_allow_html=True)
                            if fig_weekly_activity_reader: st.plotly_chart(fig_weekly_activity_reader, use_container_width=True)
                            else: st.info("لا توجد بيانات.")
                        with r_col3:
                            st.markdown("<h6>إيقاع القراءة اليومي</h6>", unsafe_allow_html=True)
                            if fig_rhythm_reader: st.plotly_chart(fig_rhythm_reader, use_container_width=True)
                            else: st.info("لا توجد بيانات.")
                    else:
                        st.info("لا توجد سجلات قراءة لهذا العضو لعرض التحليلات البيانية.")


                    st.markdown("---")
                    
                    st.markdown(f'<div class="card-subheader">خريطة التزام: {selected_member_name}</div>', unsafe_allow_html=True)
                    if not member_logs_all_time.empty:
                        min_date_reader = member_logs_all_time['submission_date_dt'].min().date()
                        max_date_reader = member_logs_all_time['submission_date_dt'].max().date()
                        individual_heatmap = create_activity_heatmap(member_logs_all_time, min_date_reader, max_date_reader, title_text="")
                        st.plotly_chart(individual_heatmap, use_container_width=True, key="individual_heatmap")
                    else:
                        st.info("لا توجد سجلات قراءة لهذا العضو لعرض الخريطة الحرارية.")
    
    st.markdown("---")
    with st.expander("🖨️ تصدير تقرير أداء التحدي (PDF)"):
        if period_logs_df.empty:
            st.warning("لا يمكن تصدير تقرير لتحدي لا يحتوي على أي سجلات.")
        else:
            if st.button("🚀 إنشاء وتصدير تقرير التحدي", key="export_challenge_pdf", use_container_width=True, type="primary"):
                with st.spinner("جاري إنشاء تقرير التحدي..."):
                    pdf = PDFReporter()
                    
                    challenge_duration = (end_date_obj - start_date_obj).days
                    challenge_period_str = f"{start_date_obj.strftime('%Y-%m-%d')} إلى {end_date_obj.strftime('%Y-%m-%d')}"
                    
                    if not period_achievements_df.empty:
                        finisher_ids = period_achievements_df[period_achievements_df['achievement_type'] == 'FINISHED_COMMON_BOOK']['member_id'].unique()
                        attendee_ids = period_achievements_df[period_achievements_df['achievement_type'] == 'ATTENDED_DISCUSSION']['member_id'].unique()
                        finishers_names = members_df[members_df['members_id'].isin(finisher_ids)]['name'].tolist()
                        attendees_names = members_df[members_df['members_id'].isin(attendee_ids)]['name'].tolist()
                    
                    total_period_minutes_pdf = period_logs_df['total_minutes'].sum()
                    total_period_hours_pdf = int(total_period_minutes_pdf // 60)
                    active_participants_pdf = period_logs_df['member_id'].nunique()
                    days_passed_pdf = (date.today() - start_date_obj).days if date.today() >= start_date_obj else 0
                    avg_daily_reading_pdf = (total_period_minutes_pdf / days_passed_pdf / active_participants_pdf) if days_passed_pdf > 0 and active_participants_pdf > 0 else 0
                    total_period_quotes_pdf = period_logs_df['submitted_common_quote'].sum() + period_logs_df['submitted_other_quote'].sum()

                    challenge_kpis = {
                        "⏳ مجموع ساعات القراءة": f"{total_period_hours_pdf:,}",
                        "👥 المشاركون الفعليون": f"{active_participants_pdf}",
                        "✍️ الاقتباسات المرسلة": f"{int(total_period_quotes_pdf)}",
                        "📊 متوسط القراءة اليومي/عضو": f"{avg_daily_reading_pdf:.1f} د"
                    }

                    challenge_date_range_df_pdf = pd.DataFrame(
                        pd.date_range(start=start_date_obj, end=min(date.today(), end_date_obj), freq='D'),
                        columns=['submission_date_dt']
                    )

                    challenge_data_for_pdf = {
                        "title": selected_challenge_data.get('book_title', ''),
                        "author": selected_challenge_data.get('book_author', ''),
                        "period": challenge_period_str,
                        "duration": challenge_duration,
                        "all_participants": all_participants_names,
                        "finishers": finishers_names,
                        "attendees": attendees_names,
                        "kpis": challenge_kpis,
                        "fig_area": charts.create_growth_chart(period_logs_df, challenge_date_range_df_pdf),
                        "fig_hours": charts.create_hours_leaderboard(podium_df),
                        "fig_points": charts.create_points_leaderboard(podium_df)
                    }
                    
                    pdf.add_challenge_report(challenge_data_for_pdf)
                    
                    pdf_output = bytes(pdf.output())
                    st.session_state.pdf_file_challenge = pdf_output
                    st.rerun()

            if 'pdf_file_challenge' in st.session_state:
                pdf_file_challenge = st.session_state.pdf_file_challenge
                st.download_button(
                    label="📥 تحميل تقرير التحدي الآن",
                    data=pdf_file_challenge,
                    file_name=f"ReadingMarathon_Report_Challenge_{date.today()}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                if st.button("إغلاق", key="close_challenge_pdf"):
                    del st.session_state.pdf_file_challenge
                    st.rerun()
