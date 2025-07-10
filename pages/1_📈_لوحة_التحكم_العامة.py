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

# This CSS snippet enforces RTL layout and adds custom styles for the hero cards
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
    
    highlight_style = "color: #2980b9; font-weight: bold;"

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
st.header("📈 لوحة التحكم العامة")

# --- Dynamic Headline ---
st.markdown("---")
if not logs_df.empty and not achievements_df.empty and not members_df.empty:
    headline_html = generate_headline(logs_df.copy(), achievements_df.copy(), members_df.copy())
    st.markdown(f"<div style='background-color: #f0f2f6; padding: 15px; border-radius: 10px; text-align: center; font-size: 1.1em; color: #1c2833;'>{headline_html}</div>", unsafe_allow_html=True)
else:
    st.markdown("<div style='background-color: #f0f2f6; padding: 15px; border-radius: 10px; text-align: center; font-size: 1.1em; color: #1c2833;'>انطلق الماراثون! أهلاً بكم</div>", unsafe_allow_html=True)
st.markdown("---")


# --- KPIs Section ---
st.subheader("📊 مؤشرات الأداء الرئيسية")
kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

total_hours = 0
total_books_finished = 0
total_quotes = 0
active_members_count = 0

if not member_stats_df.empty:
    total_minutes = member_stats_df['total_reading_minutes_common'].sum() + member_stats_df['total_reading_minutes_other'].sum()
    total_hours = int(total_minutes // 60)
    total_books_finished = member_stats_df['total_common_books_read'].sum() + member_stats_df['total_other_books_read'].sum()
    total_quotes = member_stats_df['total_quotes_submitted'].sum()

if not members_df.empty:
    active_members_count = len(members_df[members_df['is_active'] == True])

kpi_col1.metric("⏳ إجمالي ساعات القراءة", f"{total_hours:,}")
kpi_col2.metric("📚 إجمالي الكتب المنهَاة", f"{int(total_books_finished):,}")
kpi_col3.metric("✍️ إجمالي الاقتباسات", f"{int(total_quotes):,}")
kpi_col4.metric("👥 الأعضاء النشطون", f"{active_members_count}")
st.markdown("---")


# --- Hall of Fame Section ---
st.subheader("🌟 لوحة شرف الأبطال")

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

# Prepare data for calculations
if not member_stats_df.empty and not logs_df.empty and 'name' in member_stats_df.columns:
    # THE FIX IS HERE: Use left_on and right_on for the merge
    logs_with_names = pd.merge(logs_df, members_df[['members_id', 'name']], left_on='member_id', right_on='members_id', how='left')

    # 1. Mastermind (Points)
    hero_points = member_stats_df.loc[member_stats_df['total_points'].idxmax()]
    display_hero(heroes_col1, "🧠 العقل المدبّر", hero_points['name'], f"{int(hero_points['total_points'])} نقطة")

    # 2. Lord of the Hours (Total Reading Time)
    member_stats_df['total_reading_minutes'] = member_stats_df['total_reading_minutes_common'] + member_stats_df['total_reading_minutes_other']
    hero_hours = member_stats_df.loc[member_stats_df['total_reading_minutes'].idxmax()]
    display_hero(heroes_col2, "⏳ سيد الساعات", hero_hours['name'], f"{hero_hours['total_reading_minutes'] / 60:.1f} ساعة")

    # 3. Bookworm (Total Books)
    member_stats_df['total_books_read'] = member_stats_df['total_common_books_read'] + member_stats_df['total_other_books_read']
    hero_books = member_stats_df.loc[member_stats_df['total_books_read'].idxmax()]
    display_hero(heroes_col3, "📚 الديدان القارئ", hero_books['name'], f"{int(hero_books['total_books_read'])} كتب")

    # 4. Pearl Hunter (Total Quotes)
    hero_quotes = member_stats_df.loc[member_stats_df['total_quotes_submitted'].idxmax()]
    display_hero(heroes_col4, "💎 صائد الدرر", hero_quotes['name'], f"{int(hero_quotes['total_quotes_submitted'])} اقتباساً")

    # 5. The Long-Hauler (Consistency)
    consistency = logs_with_names.groupby('name')['submission_date_dt'].nunique().reset_index()
    hero_consistency = consistency.loc[consistency['submission_date_dt'].idxmax()]
    display_hero(heroes_col1, "🏃‍♂️ صاحب النَفَس الطويل", hero_consistency['name'], f"{hero_consistency['submission_date_dt']} يوم قراءة")

    # 6. The Sprinter (Best Single Day)
    daily_sum = logs_with_names.groupby(['name', pd.Grouper(key='submission_date_dt', freq='D')])['total_minutes'].sum().reset_index()
    if not daily_sum.empty:
        hero_daily = daily_sum.loc[daily_sum['total_minutes'].idxmax()]
        display_hero(heroes_col2, "⚡ العدّاء السريع", hero_daily['name'], f"{hero_daily['total_minutes'] / 60:.1f} ساعة في يوم")
    else:
        display_hero(heroes_col2, "⚡ العدّاء السريع", "لا يوجد", "0 ساعة في يوم")

    # 7. Star of the Week (Best Single Week)
    weekly_sum = logs_with_names.groupby(['name', pd.Grouper(key='submission_date_dt', freq='W-SAT')])['total_minutes'].sum().reset_index()
    if not weekly_sum.empty:
        hero_weekly = weekly_sum.loc[weekly_sum['total_minutes'].idxmax()]
        display_hero(heroes_col3, "⭐ نجم الأسبوع", hero_weekly['name'], f"{hero_weekly['total_minutes'] / 60:.1f} ساعة في أسبوع")
    else:
         display_hero(heroes_col3, "⭐ نجم الأسبوع", "لا يوجد", "0 ساعة في أسبوع")

    # 8. Giant of the Month (Best Single Month)
    monthly_sum = logs_with_names.groupby(['name', pd.Grouper(key='submission_date_dt', freq='M')])['total_minutes'].sum().reset_index()
    if not monthly_sum.empty:
        hero_monthly = monthly_sum.loc[monthly_sum['total_minutes'].idxmax()]
        display_hero(heroes_col4, "💪 عملاق الشهر", hero_monthly['name'], f"{hero_monthly['total_minutes'] / 60:.1f} ساعة في شهر")
    else:
        display_hero(heroes_col4, "💪 عملاق الشهر", "لا يوجد", "0 ساعة في شهر")

else:
    st.info("لا توجد بيانات كافية لعرض لوحة شرف الأبطال بعد.")

st.markdown("---")


# --- Charts Section ---
st.subheader("📈 تحليلات ورسوم بيانية")
charts_col1, charts_col2 = st.columns(2, gap="large")

fig_rhythm, fig_donut = None, None

with charts_col1:
    st.markdown("##### إيقاع القراءة اليومي للفريق")
    if not logs_df.empty:
        daily_team_minutes = logs_df.groupby(logs_df['submission_date_dt'].dt.date)['total_minutes'].sum().reset_index()
        daily_team_minutes.rename(columns={'submission_date_dt': 'التاريخ', 'total_minutes': 'مجموع الدقائق'}, inplace=True)
        daily_team_minutes['مجموع الساعات'] = daily_team_minutes['مجموع الدقائق'] / 60
        
        fig_rhythm = px.line(daily_team_minutes, x='التاريخ', y='مجموع الساعات',
                             labels={'التاريخ': 'التاريخ', 'مجموع الساعات': 'مجموع الساعات المقروءة'},
                             markers=True, color_discrete_sequence=['#2980b9'])
        fig_rhythm.update_layout(
            title='', margin=dict(t=20, b=0, l=0, r=0), 
            yaxis={'side': 'right'},
            xaxis_title="", yaxis_title="الساعات"
        )
        st.plotly_chart(fig_rhythm, use_container_width=True)
    else:
        st.info("لا توجد بيانات لعرض المخطط.")

with charts_col2:
    st.markdown("##### تركيز القراءة (الكتاب المشترك مقابل الكتب الأخرى)")
    if not member_stats_df.empty:
        total_common_minutes = member_stats_df['total_reading_minutes_common'].sum()
        total_other_minutes = member_stats_df['total_reading_minutes_other'].sum()
        if total_common_minutes > 0 or total_other_minutes > 0:
            donut_labels = ['الكتاب المشترك', 'الكتب الأخرى']
            donut_values = [total_common_minutes, total_other_minutes]
            colors = ['#3498db', '#f1c40f']
            fig_donut = go.Figure(data=[go.Pie(labels=donut_labels, values=donut_values, hole=.5, marker_colors=colors)])
            fig_donut.update_layout(showlegend=True, legend=dict(x=0.5, y=-0.1, xanchor='center', orientation='h'), margin=dict(t=20, b=20, l=20, r=20), annotations=[dict(text='التوزيع', x=0.5, y=0.5, font_size=14, showarrow=False)])
            st.plotly_chart(fig_donut, use_container_width=True)
        else:
            st.info("لا توجد بيانات.")
    else:
        st.info("لا توجد بيانات.")

st.markdown("---")
# --- Leaderboards Section ---
st.subheader("🏆 قوائم المتصدرين")
leader_col1, leader_col2 = st.columns(2, gap="large")

fig_points_leaderboard, fig_hours_leaderboard = None, None

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
    
    # Note: PDF export logic needs to be updated to include the new heroes and charts.
    # This is a placeholder for now.
    if st.button("🚀 إنشاء وتصدير تقرير لوحة التحكم", use_container_width=True, type="primary"):
        with st.spinner("جاري إنشاء التقرير..."):
            pdf = PDFReporter()
            
            # This part needs refactoring to pass the new hero data to the PDF reporter
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

            kpis_main = {
                "⏳ إجمالي ساعات القراءة": f"{total_hours:,}",
                "📚 إجمالي الكتب المنهَاة": f"{int(total_books_finished):,}",
                "✍️ إجمالي الاقتباسات": f"{int(total_quotes):,}"
            }
            completed_challenges_count = 0
            if not periods_df.empty:
                today_date = date.today()
                periods_df['end_date_dt'] = pd.to_datetime(periods_df['end_date']).dt.date
                completed_challenges_count = len(periods_df[periods_df['end_date_dt'] < today_date])
            total_reading_days = len(logs_df['submission_date'].unique()) if not logs_df.empty else 0
            kpis_secondary = {
                "👥 الأعضاء النشطون": f"{active_members_count}",
                "🏁 التحديات المكتملة": f"{completed_challenges_count}",
                "🗓️ أيام القراءة": f"{total_reading_days}"
            }
            group_stats_for_pdf = {
                "total": len(members_df),
                "active": active_members_count,
                "inactive": len(members_df) - active_members_count,
            }

            # The old charts are no longer generated, so we pass None for now.
            # This needs to be updated in the PDF class itself in a future step.
            fig_growth, fig_bar_days = None, None

            dashboard_data = {
                "kpis_main": kpis_main,
                "kpis_secondary": kpis_secondary,
                "champions_data": champions_data,
                "fig_growth": fig_growth, 
                "fig_donut": fig_donut,
                "fig_bar_days": fig_bar_days,
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