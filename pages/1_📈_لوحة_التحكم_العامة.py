import streamlit as st
import pandas as pd
from datetime import date, timedelta
import db_manager as db
import plotly.express as px
import plotly.graph_objects as go
from pdf_reporter import PDFReporter

st.set_page_config(
    page_title="لوحة التحكم العامة",
    page_icon="📈"
)


# This CSS snippet enforces RTL layout across the app
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
    </style>
""", unsafe_allow_html=True)



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

    last_7_days_logs = logs_df[logs_df['submission_date_dt'] >= last_7_days_start]
    prev_7_days_logs = logs_df[(logs_df['submission_date_dt'] >= prev_7_days_start) & (logs_df['submission_date_dt'] <= prev_7_days_end)]
    
    last_7_total_minutes = last_7_days_logs['total_minutes'].sum()
    prev_7_total_minutes = prev_7_days_logs['total_minutes'].sum()

    momentum_available = prev_7_total_minutes > 0
    momentum_positive = None
    percentage_change = 0
    if momentum_available:
        percentage_change = ((last_7_total_minutes - prev_7_total_minutes) / prev_7_total_minutes) * 100
        momentum_positive = percentage_change >= 0

    recent_achievements = achievements_df[achievements_df['achievement_date_dt'] >= last_7_days_start]
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

# --- Check if user is logged in ---
if 'user_id' not in st.session_state or not st.session_state.user_id:
    st.error("يرجى تسجيل الدخول أولاً للوصول إلى هذه الصفحة.")
    st.stop()

user_id = st.session_state.user_id

# --- Data Loading ---
@st.cache_data(ttl=300) # Cache data for 5 minutes
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
    logs_df['submission_date_dt'] = pd.to_datetime(logs_df['submission_date'], format='%d/%m/%Y', errors='coerce').dt.date
    logs_df['weekday_name'] = pd.to_datetime(logs_df['submission_date_dt']).dt.strftime('%A')
    logs_df['total_minutes'] = logs_df['common_book_minutes'] + logs_df['other_book_minutes']

if not achievements_df.empty:
    achievements_df['achievement_date_dt'] = pd.to_datetime(achievements_df['achievement_date'], errors='coerce').dt.date
    
if not member_stats_df.empty and not members_df.empty:
    member_stats_df.rename(columns={'member_stats_id': 'members_id'}, inplace=True, errors='ignore')
    member_stats_df = pd.merge(member_stats_df, members_df[['members_id', 'name']], on='members_id', how='left')


# --- Page Rendering ---
st.header("📈 لوحة التحكم العامة")

if not member_stats_df.empty:
    total_minutes = member_stats_df['total_reading_minutes_common'].sum() + member_stats_df['total_reading_minutes_other'].sum()
    total_hours = int(total_minutes // 60)
    total_books_finished = member_stats_df['total_common_books_read'].sum() + member_stats_df['total_other_books_read'].sum()
    total_quotes = member_stats_df['total_quotes_submitted'].sum()
    member_stats_df['total_reading_minutes'] = member_stats_df['total_reading_minutes_common'] + member_stats_df['total_reading_minutes_other']
    member_stats_df['total_books_read'] = member_stats_df['total_common_books_read'] + member_stats_df['total_other_books_read']
    king_of_reading = member_stats_df.loc[member_stats_df['total_reading_minutes'].idxmax()]
    king_of_books = member_stats_df.loc[member_stats_df['total_books_read'].idxmax()]
    king_of_points = member_stats_df.loc[member_stats_df['total_points'].idxmax()]
    king_of_quotes = member_stats_df.loc[member_stats_df['total_quotes_submitted'].idxmax()]
else:
    total_hours, total_books_finished, total_quotes = 0, 0, 0
    king_of_reading, king_of_books, king_of_points, king_of_quotes = [pd.Series(dtype=object)]*4

active_members_count = 0
if not members_df.empty:
    active_members_count = len(members_df[members_df['is_active'] == True])

completed_challenges_count = 0
if not periods_df.empty:
    today_date = date.today()
    periods_df['end_date_dt'] = pd.to_datetime(periods_df['end_date']).dt.date
    completed_challenges_count = len(periods_df[periods_df['end_date_dt'] < today_date])

total_reading_days = len(logs_df['submission_date'].unique()) if not logs_df.empty else 0

st.markdown("---")
if not logs_df.empty and not achievements_df.empty and not members_df.empty:
    headline_html = generate_headline(logs_df.copy(), achievements_df.copy(), members_df.copy())
    st.markdown(f"<div style='background-color: #f0f2f6; padding: 15px; border-radius: 10px; text-align: center; font-size: 1.1em; color: #1c2833;'>{headline_html}</div>", unsafe_allow_html=True)
else:
    st.markdown("<div style='background-color: #f0f2f6; padding: 15px; border-radius: 10px; text-align: center; font-size: 1.1em; color: #1c2833;'>انطلق الماراثون! أهلاً بكم</div>", unsafe_allow_html=True)
st.markdown("---")

col1, col2 = st.columns([1.5, 1], gap="large")
with col1:
    st.subheader("📊 مؤشرات الأداء الرئيسية")
    kpis_main = {
        "⏳ إجمالي ساعات القراءة": f"{total_hours:,}",
        "📚 إجمالي الكتب المنهَاة": f"{total_books_finished:,}",
        "✍️ إجمالي الاقتباسات": f"{total_quotes:,}"
    }
    kpis_secondary = {
        "👥 الأعضاء النشطون": f"{active_members_count}",
        "🏁 التحديات المكتملة": f"{completed_challenges_count}",
        "🗓️ أيام القراءة": f"{total_reading_days}"
    }
    kpi1, kpi2, kpi3 = st.columns(3)
    for col, (label, value) in zip([kpi1, kpi2, kpi3], kpis_main.items()):
        col.metric(label=label, value=value)
    
    kpi4, kpi5, kpi6 = st.columns(3)
    for col, (label, value) in zip([kpi4, kpi5, kpi6], kpis_secondary.items()):
        col.metric(label=label, value=value)

with col2:
    st.subheader("🏆 أبطال الماراثون")
    if not king_of_reading.empty and king_of_reading.get('name'):
        sub_col1, sub_col2 = st.columns(2)
        with sub_col1:
            st.metric(label="👑 ملك القراءة", value=king_of_reading.get('name', 'N/A'))
            st.metric(label="⭐ ملك النقاط", value=king_of_points.get('name', 'N/A'))
        with sub_col2:
            st.metric(label="📚 ملك الكتب", value=king_of_books.get('name', 'N/A'))
            st.metric(label="✍️ ملك الاقتباسات", value=king_of_quotes.get('name', 'N/A'))
    else:
        st.info("لا أبطال بعد.")

st.markdown("---")

col_growth, col_donut, col_days = st.columns([2, 1, 1], gap="large")
fig_growth, fig_donut, fig_bar_days = None, None, None
with col_growth:
    st.subheader("📈 نمو القراءة التراكمي")
    if not logs_df.empty:
        daily_minutes = logs_df.groupby('submission_date_dt')['total_minutes'].sum().reset_index(name='minutes')
        daily_minutes = daily_minutes.sort_values('submission_date_dt')
        daily_minutes['cumulative_hours'] = daily_minutes['minutes'].cumsum() / 60
        fig_growth = px.area(daily_minutes, x='submission_date_dt', y='cumulative_hours', 
                             labels={'submission_date_dt': 'التاريخ', 'cumulative_hours': 'مجموع الساعات'},
                             markers=False, color_discrete_sequence=['#2980b9'])
        fig_growth.update_layout(title='', margin=dict(t=20, b=0, l=0, r=0), xaxis_autorange='reversed', yaxis={'side': 'right'})
        st.plotly_chart(fig_growth, use_container_width=True)
    else:
        st.info("لا توجد بيانات لعرض المخطط.")
        
with col_donut:
    st.subheader("🎯 تركيز القراءة")
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

with col_days:
    st.subheader("📅 أيام النشاط")
    if not logs_df.empty:
        weekday_map_ar = {"Saturday": "السبت", "Sunday": "الأحد", "Monday": "الاثنين", "Tuesday": "الثلاثاء", "Wednesday": "الأربعاء", "Thursday": "الخميس", "Friday": "الجمعة"}
        weekday_order_ar = ["الجمعة", "الخميس", "الأربعاء", "الثلاثاء", "الاثنين", "الأحد", "السبت"]
        logs_df['weekday_ar'] = logs_df['weekday_name'].map(weekday_map_ar)
        daily_activity_hours = (logs_df.groupby('weekday_ar', observed=False)['total_minutes'].sum() / 60).reindex(weekday_order_ar).fillna(0)
        
        fig_bar_days = px.bar(daily_activity_hours, x=daily_activity_hours.index, y=daily_activity_hours.values, 
                              color_discrete_sequence=['#1abc9c'])
        
        fig_bar_days.update_layout(
            margin=dict(t=20, b=0, l=0, r=0), 
            title='', 
            yaxis={'side': 'right'},
            xaxis_title="أيام الأسبوع",
            yaxis_title="الساعات"
        )
        st.plotly_chart(fig_bar_days, use_container_width=True)
    else:
        st.info("لا توجد بيانات.")
st.markdown("---")

col_points, col_hours = st.columns(2, gap="large")
points_leaderboard_df, hours_leaderboard_df = pd.DataFrame(), pd.DataFrame()
with col_points:
    st.subheader("⭐ المتصدرون بالنقاط")
    if not member_stats_df.empty:
        points_leaderboard_df = member_stats_df.sort_values('total_points', ascending=False).head(10)[['name', 'total_points']].rename(columns={'name': 'الاسم', 'total_points': 'النقاط'})
        fig_points_leaderboard = px.bar(points_leaderboard_df, x='النقاط', y='الاسم', orientation='h', 
                                        text='النقاط', color_discrete_sequence=['#9b59b6'])
        fig_points_leaderboard.update_traces(textposition='outside')
        fig_points_leaderboard.update_layout(title='', yaxis={'side': 'right', 'autorange': 'reversed'}, xaxis_autorange='reversed', margin=dict(t=20, b=0, l=0, r=0))
        st.plotly_chart(fig_points_leaderboard, use_container_width=True)
    else:
        st.info("لا توجد بيانات.")
with col_hours:
    st.subheader("⏳ المتصدرون بالساعات")
    if not member_stats_df.empty:
        member_stats_df['total_hours'] = member_stats_df['total_reading_minutes'] / 60
        hours_leaderboard_df = member_stats_df.sort_values('total_hours', ascending=False).head(10)[['name', 'total_hours']].rename(columns={'name': 'الاسم', 'total_hours': 'الساعات'})
        hours_leaderboard_df['الساعات'] = hours_leaderboard_df['الساعات'].round(1)
        fig_hours_leaderboard = px.bar(hours_leaderboard_df, x='الساعات', y='الاسم', orientation='h', 
                                       text='الساعات', color_discrete_sequence=['#e67e22'])
        fig_hours_leaderboard.update_traces(texttemplate='%{text:.1f}', textposition='outside')
        fig_hours_leaderboard.update_layout(title='', yaxis={'side': 'right', 'autorange': 'reversed'}, margin=dict(t=20, b=0, l=0, r=0))
        st.plotly_chart(fig_hours_leaderboard, use_container_width=True)
    else:
        st.info("لا توجد بيانات.")

group_stats_for_pdf = {
    "total": len(members_df),
    "active": active_members_count,
    "inactive": len(members_df) - active_members_count,
}

st.markdown("---")
with st.expander("🖨️ تصدير تقرير الأداء (PDF)"):
    st.info("اضغط على الزر أدناه لتصدير تقرير شامل للوحة التحكم العامة.")
    
    if st.button("🚀 إنشاء وتصدير تقرير لوحة التحكم", use_container_width=True, type="primary"):
        with st.spinner("جاري إنشاء التقرير..."):
            pdf = PDFReporter()
            
            champions_data = {}
            if not king_of_reading.empty and king_of_reading.get('name'): champions_data["👑 ملك القراءة"] = king_of_reading.get('name', 'N/A')
            if not king_of_points.empty and king_of_points.get('name'): champions_data["⭐ ملك النقاط"] = king_of_points.get('name', 'N/A')
            if not king_of_books.empty and king_of_books.get('name'): champions_data["📚 ملك الكتب"] = king_of_books.get('name', 'N/A')
            if not king_of_quotes.empty and king_of_quotes.get('name'): champions_data["✍️ ملك الاقتباسات"] = king_of_quotes.get('name', 'N/A')
            
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
            # Use a toast for quick feedback and rerun to show the download button
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
