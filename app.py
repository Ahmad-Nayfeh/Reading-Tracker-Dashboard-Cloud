import streamlit as st
import pandas as pd
from datetime import date, timedelta, datetime
import db_manager as db
import plotly.express as px
import plotly.graph_objects as go
from main import run_data_update
import auth_manager
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import gspread
import time
import locale
import base64

# Import the new PDF reporter class
from pdf_reporter import PDFReporter

# --- Page Configuration and RTL CSS Injection ---
st.set_page_config(page_title="ماراثون القراءة", page_icon="📚", layout="wide")

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


# --- Helper function for Date Dropdown ---
def generate_date_options():
    today_obj = date.today()
    dates = []
    arabic_days = {"Monday": "الاثنين", "Tuesday": "الثلاثاء", "Wednesday": "الأربعاء", "Thursday": "الخميس", "Friday": "الجمعة", "Saturday": "السبت", "Sunday": "الأحد"}
    for i in range(7):
        current = today_obj - timedelta(days=i)
        english_day_name = current.strftime('%A')
        arabic_day_name = arabic_days.get(english_day_name, english_day_name)
        dates.append(f"{current.strftime('%Y-%m-%d')} ({arabic_day_name})")
    return dates

# --- MODIFIED: Helper function to create Activity Heatmap with RTL support ---
def create_activity_heatmap(df, start_date, end_date, title_text=''):
    df = df.copy()
    if df.empty:
        return go.Figure().update_layout(title="لا توجد بيانات قراءة لعرضها في الخريطة")

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

    fig.update_layout(
        title=title_text,
        xaxis_title='أسابيع التحدي',
        yaxis_title='',
        xaxis_autorange='reversed',
        yaxis={'side': 'right'},
        xaxis=dict(tickmode='array', tickvals=list(month_positions.week_of_year), ticktext=list(month_positions.index)),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='#333',
        margin=dict(l=80)
    )
    return fig

# --- Helper function to update Google Form ---
def update_form_members(forms_service, form_id, question_id, active_member_names):
    if not form_id or not question_id:
        st.error("لم يتم العثور على معرّف النموذج أو معرّف سؤال الأعضاء في الإعدادات.")
        return False
    
    update_request = {
        "requests": [
            {
                "updateItem": {
                    "item": {
                        "itemId": question_id,
                        "questionItem": {
                            "question": {
                                "choiceQuestion": {
                                    "type": "DROP_DOWN",
                                    "options": [{"value": name} for name in sorted(active_member_names)]
                                }
                            }
                        }
                    },
                    "location": {"index": 0}, 
                    "updateMask": "questionItem.question.choiceQuestion.options"
                }
            }
        ]
    }
    
    try:
        forms_service.forms().batchUpdate(formId=form_id, body=update_request).execute()
        return True
    except HttpError as e:
        st.error(f"⚠️ فشل تحديث نموذج جوجل: {e}")
        return False
    except Exception as e:
        st.error(f"حدث خطأ غير متوقع أثناء تحديث النموذج: {e}")
        return False

# --- FINALIZED: Helper function for Dynamic Headline (Overall Dashboard) ---
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

# --- FINALIZED: Helper function for Challenge Headline ---
def generate_challenge_headline(podium_df, period_achievements_df, members_df, end_date_obj):
    today = date.today()
    highlight_style = "color: #2980b9; font-weight: bold;"
    
    quoter_part = ""
    if not podium_df.empty and podium_df['quotes'].sum() > 0:
        top_quoter = podium_df.loc[podium_df['quotes'].idxmax()]
        quoter_part = f"<span style='{highlight_style}'>{top_quoter['name']}</span> يتصدر سباق الاقتباسات"

    finishers_part = ""
    if not period_achievements_df.empty:
        finishers_df = period_achievements_df[period_achievements_df['achievement_type'] == 'FINISHED_COMMON_BOOK'].sort_values(by='achievement_date')
        if not finishers_df.empty:
            finisher_ids = finishers_df['member_id'].tolist()
            finisher_names = [members_df[members_df['members_id'] == mid].iloc[0]['name'] for mid in finisher_ids]
            n = len(finisher_names)
            names_hl = [f"<span style='{highlight_style}'>{name}</span>" for name in finisher_names]
            
            if n == 1:
                finishers_part = f"وعلى الطرف الآخر {names_hl[0]} كان أول من أنهى الكتاب"
            elif n == 2:
                finishers_part = f"وعلى الطرف الآخر {names_hl[0]} كان أول من أنهى الكتاب، وتبعه في ذلك {names_hl[1]}"
            elif n == 3:
                finishers_part = f"وعلى الطرف الآخر {names_hl[0]} كان أول من أنهى الكتاب، وتبعه في ذلك {names_hl[1]}، ثم {names_hl[2]}"
            else: # n >= 4
                finishers_part = f"وعلى الطرف الآخر <span style='{highlight_style}'>{n}</span> أعضاء أنهوا الكتاب وعلى رأسهم {names_hl[0]}"

    discussion_part = ""
    if today > end_date_obj:
        if not period_achievements_df.empty:
            attendees_df = period_achievements_df[period_achievements_df['achievement_type'] == 'ATTENDED_DISCUSSION']
            attendee_ids = attendees_df['member_id'].tolist()
            attendee_names = [members_df[members_df['members_id'] == mid].iloc[0]['name'] for mid in attendee_ids]
            n_attendees = len(attendee_names)
            names_hl = [f"<span style='{highlight_style}'>{name}</span>" for name in attendee_names]

            if n_attendees == 0:
                discussion_part = "ولكن للأسف لم تنعقد جلسة النقاش"
            elif n_attendees == 1:
                discussion_part = f"ولكن لسبب غريب لم يحضر إلا {names_hl[0]} إلى جلسة النقاش"
            elif n_attendees == 2:
                discussion_part = f"ولكن لم يحضر إلا {names_hl[0]} و {names_hl[1]} إلى جلسة النقاش"
            elif n_attendees == 3:
                discussion_part = f"وانعقدت جلسة النقاش وحضرها {names_hl[0]} و {names_hl[1]} و {names_hl[2]}"
            elif 4 <= n_attendees <= 10:
                discussion_part = f"وانعقدت جلسة النقاش وحضرها <span style='{highlight_style}'>{n_attendees}</span> أعضاء"
            else: # n_attendees >= 11
                discussion_part = f"وانعقدت جلسة النقاش وحضرها <span style='{highlight_style}'>{n_attendees}</span> عضو"

    final_parts = [p for p in [quoter_part, finishers_part] if p]
    
    if len(final_parts) == 0:
        final_text = "التحدي في بدايته، كل الإنجازات ممكنة"
    elif len(final_parts) == 1:
        final_text = final_parts[0]
    elif len(final_parts) == 2:
        final_text = f"{final_parts[0]}، {final_parts[1]}"

    if discussion_part:
        if final_text == "التحدي في بدايته، كل الإنجازات ممكنة":
             final_text = discussion_part
        else:
            final_text = f"{final_text}، {discussion_part}"
    
    style = "background-color: #eaf2f8; padding: 15px; border-radius: 10px; text-align: center; font-size: 1.1em; color: #1c2833;"
    return f"<div style='{style}'>{final_text}</div>"
    
# --- Main App Authentication and Setup ---
creds = auth_manager.authenticate()

user_id = st.session_state.get('user_id')
user_email = st.session_state.get('user_email')

if not user_id:
    st.error("خطأ: لم يتم تحديد هوية المستخدم. يرجى محاولة إعادة تحميل الصفحة.")
    st.stop()

gc = auth_manager.get_gspread_client()
forms_service = build('forms', 'v1', credentials=creds)

user_settings = db.get_user_settings(user_id)
spreadsheet_url = user_settings.get("spreadsheet_url")
form_url = user_settings.get("form_url")

all_data = db.get_all_data_for_stats(user_id)
members_df = pd.DataFrame(all_data.get('members', []))
periods_df = pd.DataFrame(all_data.get('periods', []))

members_exist = not members_df.empty
tools_exist = spreadsheet_url and form_url
challenge_exist = not periods_df.empty
setup_complete = members_exist and tools_exist and challenge_exist

st.sidebar.title("لوحة التحكم")
st.sidebar.success(f"أهلاً بك! {user_email}")
st.sidebar.divider()

if not setup_complete:
    st.title("🚀 مرحباً بك في ماراثون القراءة!")
    st.info("لتجهيز مساحة العمل الخاصة بك، يرجى اتباع الخطوات التالية:")

    if not members_exist:
        st.header("الخطوة 1: إضافة أعضاء فريقك")
        st.warning("قبل المتابعة، يجب إضافة عضو واحد على الأقل.")
        with st.form("initial_members_form"):
            names_str = st.text_area("أدخل أسماء المشاركين (كل اسم في سطر جديد):", height=150, placeholder="خالد\nسارة\n...")
            if st.form_submit_button("إضافة الأعضاء وحفظهم", use_container_width=True, type="primary"):
                names = [name.strip() for name in names_str.split('\n') if name.strip()]
                if names:
                    with st.spinner("جاري إضافة الأعضاء..."):
                        db.add_members(user_id, names)
                    st.success("تمت إضافة الأعضاء بنجاح! سيتم تحديث الصفحة للمتابعة إلى الخطوة التالية.")
                    st.balloons()
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("يرجى إدخال اسم واحد على الأقل.")
        st.stop()

    if not tools_exist:
        st.header("الخطوة 2: إنشاء أدوات جوجل")
        st.info("سيقوم التطبيق الآن بإنشاء جدول بيانات (Google Sheet) ونموذج تسجيل (Google Form) في حسابك.")
        if 'sheet_title' not in st.session_state:
            st.session_state.sheet_title = f"بيانات ماراثون القراءة - {user_email.split('@')[0]}"
        st.session_state.sheet_title = st.text_input("اختر اسماً لأدواتك (سيتم تطبيقه على الشيت والفورم):", value=st.session_state.sheet_title)
        
        if st.button("📝 إنشاء الشيت والفورم الآن", type="primary", use_container_width=True):
            with st.spinner("جاري إنشاء جدول البيانات..."):
                try:
                    spreadsheet = gc.create(st.session_state.sheet_title)
                    db.set_user_setting(user_id, "spreadsheet_url", spreadsheet.url)
                    st.success("✅ تم إنشاء جدول البيانات بنجاح!")
                except Exception as e:
                    st.error(f"🌐 خطأ في إنشاء الشيت: {e}")
                    st.stop()
            
            with st.spinner("جاري إنشاء نموذج التسجيل..."):
                try:
                    member_names = members_df['name'].tolist()
                    new_form_info = {"info": {"title": st.session_state.sheet_title, "documentTitle": st.session_state.sheet_title}}
                    form_result = forms_service.forms().create(body=new_form_info).execute()
                    form_id = form_result['formId']
                    date_options = generate_date_options()
                    
                    update_requests = {"requests": [
                        {"updateFormInfo": {"info": {"description": "يرجى ملء هذا النموذج يومياً لتسجيل نشاطك في تحدي القراءة. بالتوفيق!"}, "updateMask": "description"}},
                        {"createItem": {"item": {"title": "اسمك", "questionItem": {"question": {"required": True, "choiceQuestion": {"type": "DROP_DOWN", "options": [{"value": name} for name in member_names]}}}}, "location": {"index": 0}}},
                        
                        {"createItem": {"item": {
                            "title": "تاريخ القراءة",
                            "questionItem": {"question": {
                                "required": True,
                                "dateQuestion": {
                                    # هذا هو الخيار الأهم الذي يضمن عدم ظهور مربع إدخال الوقت
                                    "includeTime": False,
                                    "includeYear": True
                                }
                            }}
                        }, "location": {"index": 1}}},                        
                        {"createItem": {"item": {"title": "مدة قراءة الكتاب المشترك (اختياري)", "questionItem": {"question": {"timeQuestion": {"duration": True}}}}, "location": {"index": 2}}},
                        {"createItem": {"item": {"title": "مدة قراءة كتاب آخر (اختياري)", "questionItem": {"question": {"timeQuestion": {"duration": True}}}}, "location": {"index": 3}}},
                        {"createItem": {"item": {"title": "ما هي الاقتباسات التي أرسلتها اليوم؟ (اختياري)", "questionItem": {"question": {"choiceQuestion": {"type": "CHECKBOX", "options": [{"value": "أرسلت اقتباساً من الكتاب المشترك"}, {"value": "أرسلت اقتباساً من كتاب آخر"}]}}}}, "location": {"index": 4}}},
                        {"createItem": {"item": {"title": "إنجازات الكتب والنقاش (اختر فقط عند حدوثه لأول مرة)", "questionItem": {"question": {"choiceQuestion": {"type": "CHECKBOX", "options": [{"value": "أنهيت الكتاب المشترك"}, {"value": "أنهيت كتاباً آخر"}, {"value": "حضرت جلسة النقاش"}]}}}}, "location": {"index": 5}}}
                    ]}
                    
                    update_result = forms_service.forms().batchUpdate(formId=form_id, body=update_requests).execute()
                    
                    member_question_id = update_result['replies'][1]['createItem']['itemId']
                    db.set_user_setting(user_id, "form_id", form_id)
                    db.set_user_setting(user_id, "member_question_id", member_question_id)
                    db.set_user_setting(user_id, "form_url", form_result['responderUri'])
                    
                    st.success("✅ تم إنشاء النموذج وحفظ إعداداته بنجاح!")
                except Exception as e:
                    st.error(f"🌐 خطأ في إنشاء الفورم: {e}")
                    st.stop()

            st.header("🔗 الخطوة الأخيرة: الربط والتحقق")
            st.warning("هذه الخطوات ضرورية جداً ويجب القيام بها مرة واحدة فقط.")
            editor_url = f"https://docs.google.com/forms/d/{form_id}/edit"
            
            st.write("1. **افتح النموذج للتعديل** من الرابط أدناه:")
            st.code(editor_url)
            st.write("2. انتقل إلى تبويب **\"الردود\" (Responses)**.")
            st.write("3. اضغط على أيقونة **'Link to Sheets'** (أيقونة جدول البيانات الخضراء).")
            st.write("4. اختر **'Select existing spreadsheet'** وقم باختيار جدول البيانات الذي أنشأته للتو بنفس الاسم.")
            st.write("5. **(خطوة هامة لضمان عمل التواريخ بشكل صحيح)** افتح جدول البيانات، ومن القائمة العلوية اذهب إلى **File > Settings**، ثم غيّر الـ **Locale** إلى **United Kingdom** واضغط **Save settings**. هذا يضمن أن كل التواريخ ستُكتب بصيغة (DD/MM/YYYY).")

            if st.button("تحقق من الربط وتابع", type="primary", use_container_width=True):
                with st.spinner("جاري التحقق من ربط النموذج بجدول البيانات..."):
                    try:
                        spreadsheet = gc.open_by_url(spreadsheet_url)
                        
                        # قائمة بأسماء أوراق العمل المحتملة التي سيبحث عنها التطبيق
                        POSSIBLE_SHEET_NAMES = ["Form Responses 1", "Form responses 1", "ردود النموذج 1"]
                        
                        all_worksheets = spreadsheet.worksheets()
                        found_sheet = None
                        for sheet in all_worksheets:
                            if sheet.title in POSSIBLE_SHEET_NAMES:
                                found_sheet = sheet
                                break

                        if found_sheet:
                            st.success(f"✅ تم التحقق بنجاح! تم العثور على ورقة الردود باسم: '{found_sheet.title}'.")
                            
                            # محاولة تنظيف الصفحة الافتراضية "Sheet1"
                            try:
                                default_sheet = spreadsheet.worksheet('Sheet1')
                                spreadsheet.del_worksheet(default_sheet)
                                st.info("ℹ️ تم حذف ورقة 'Sheet1' الفارغة بنجاح.")
                            except gspread.exceptions.WorksheetNotFound:
                                pass # الورقة غير موجودة، وهذا جيد
                            
                            time.sleep(2)
                            st.rerun()
                        else:
                            # إذا لم يتم العثور على ورقة متوقعة، أظهر خطأ للمستخدم
                            sheet_titles = [s.title for s in all_worksheets]
                            st.error(
                                "❌ فشل التحقق. لم يتم العثور على ورقة ردود بالأسماء المتوقعة. "
                                f"الأسماء التي وجدناها هي: {', '.join(sheet_titles)}. "
                                "يرجى التأكد من اسم الورقة التي تم إنشاؤها وتغييره إلى 'Form Responses 1' ثم المحاولة مرة أخرى."
                            )

                    except Exception as e:
                        st.error(f"حدث خطأ أثناء محاولة الوصول لجدول البيانات: {e}")
            st.stop()

    if not challenge_exist:
        st.header("الخطوة 3: إنشاء أول تحدي لك")
        st.info("أنت على وشك الانتهاء! كل ما عليك فعله هو إضافة تفاصيل أول كتاب وتحدي للبدء.")
        with st.form("new_challenge_form", clear_on_submit=True):
            st.text_input("عنوان الكتاب المشترك الأول", key="book_title")
            st.text_input("اسم المؤلف", key="book_author")
            st.number_input("سنة النشر", key="pub_year", value=date.today().year, step=1)
            st.date_input("تاريخ بداية التحدي", key="start_date", value=date.today())
            st.date_input("تاريخ نهاية التحدي", key="end_date", value=date.today() + timedelta(days=30))
            if st.form_submit_button("بدء التحدي الأول!", use_container_width=True, type="primary"):
                if st.session_state.book_title and st.session_state.book_author:
                    book_info = {'title': st.session_state.book_title, 'author': st.session_state.book_author, 'year': st.session_state.pub_year}
                    challenge_info = {'start_date': str(st.session_state.start_date), 'end_date': str(st.session_state.end_date)}
                    default_rules = db.load_user_global_rules(user_id)
                    if default_rules:
                        success, message = db.add_book_and_challenge(user_id, book_info, challenge_info, default_rules)
                        if success:
                            st.success("🎉 اكتمل الإعداد! تم إنشاء أول تحدي بنجاح.")
                            st.balloons()
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error(f"❌ فشلت العملية: {message}")
                    else:
                        st.error("لم يتم العثور على الإعدادات الافتراضية في قاعدة البيانات.")
                else:
                    st.error("✏️ بيانات غير مكتملة: يرجى إدخال عنوان الكتاب واسم المؤلف.")
        st.stop()

if st.sidebar.button("🔄 تحديث وسحب البيانات", type="primary", use_container_width=True):
    with st.spinner("جاري سحب البيانات من Google Sheet الخاص بك..."):
        update_log = run_data_update(gc, user_id) 
        st.session_state['update_log'] = update_log
        if 'editor_data' in st.session_state:
            del st.session_state['editor_data']
    st.rerun()

if 'update_log' in st.session_state:
    st.info("اكتملت عملية المزامنة.")
    with st.expander("عرض تفاصيل سجل التحديث الأخير"):
        for message in st.session_state.update_log:
            st.text(message)
    del st.session_state['update_log']

st.sidebar.title("التنقل")
page_options = ["📈 لوحة التحكم العامة", "🎯 تحليلات التحديات", "⚙️ الإدارة والإعدادات"]
page = st.sidebar.radio("اختر صفحة لعرضها:", page_options, key="navigation")

logs_df = pd.DataFrame(all_data.get('logs', []))
if not logs_df.empty:
    logs_df['submission_date_dt'] = pd.to_datetime(logs_df['submission_date'], format='%d/%m/%Y', errors='coerce').dt.date
    logs_df['weekday_name'] = pd.to_datetime(logs_df['submission_date_dt']).dt.strftime('%A')
    logs_df['total_minutes'] = logs_df['common_book_minutes'] + logs_df['other_book_minutes']

achievements_df = pd.DataFrame(all_data.get('achievements', []))
if not achievements_df.empty:
    achievements_df['achievement_date_dt'] = pd.to_datetime(achievements_df['achievement_date'], errors='coerce').dt.date
    
member_stats_df = db.get_subcollection_as_df(user_id, 'member_stats')
if not member_stats_df.empty and not members_df.empty:
    member_stats_df.rename(columns={'member_stats_id': 'members_id'}, inplace=True, errors='ignore')
    member_stats_df = pd.merge(member_stats_df, members_df[['members_id', 'name']], on='members_id', how='left')

if page == "📈 لوحة التحكم العامة":
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
        active_members_count = len(members_df[members_df['is_active'] == 1])
    
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
        if not king_of_reading.empty:
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
            fig_hours_leaderboard.update_layout(title='', yaxis={'side': 'right', 'autorange': 'reversed'}, xaxis_autorange='reversed', margin=dict(t=20, b=0, l=0, r=0))
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
                if not king_of_reading.empty: champions_data["👑 ملك القراءة"] = king_of_reading.get('name', 'N/A')
                if not king_of_points.empty: champions_data["⭐ ملك النقاط"] = king_of_points.get('name', 'N/A')
                if not king_of_books.empty: champions_data["📚 ملك الكتب"] = king_of_books.get('name', 'N/A')
                if not king_of_quotes.empty: champions_data["✍️ ملك الاقتباسات"] = king_of_quotes.get('name', 'N/A')
                
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


elif page == "🎯 تحليلات التحديات":
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
        st.subheader(f"تحليلات تحدي: {selected_challenge_data.get('book_title', 'N/A')}")

        start_date_obj = datetime.strptime(selected_challenge_data['start_date'], '%Y-%m-%d').date()
        end_date_obj = datetime.strptime(selected_challenge_data['end_date'], '%Y-%m-%d').date()
        
        period_logs_df = pd.DataFrame()
        if not logs_df.empty:
            period_logs_df = logs_df[(logs_df['submission_date_dt'].notna()) & (logs_df['submission_date_dt'] >= start_date_obj) & (logs_df['submission_date_dt'] <= end_date_obj)].copy()
        
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
                member_id = member['members_id']
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

                total_minutes = common_minutes + other_minutes
                total_hours = total_minutes / 60
                total_quotes = common_quotes + other_quotes

                podium_data.append({'member_id': member_id, 'name': member['name'], 'points': int(points), 'hours': total_hours, 'quotes': int(total_quotes)})
            podium_df = pd.DataFrame(podium_data)

        fig_gauge, fig_area, heatmap_fig, fig_hours, fig_points = None, None, None, None, None
        total_period_hours, active_participants, total_period_quotes, avg_daily_reading = 0, 0, 0, 0
        finishers_names, attendees_names = [], []

        tab1, tab2 = st.tabs(["📝 ملخص التحدي", "🧑‍💻 بطاقة القارئ"])

        with tab1:
            if period_logs_df.empty:
                st.info("لا توجد بيانات مسجلة لهذا التحدي بعد.")
            else:
                st.markdown(generate_challenge_headline(podium_df, period_achievements_df, members_df, end_date_obj), unsafe_allow_html=True)
                st.markdown("---")

                col1, col2 = st.columns([1, 1.5], gap="large")
                with col1:
                    st.subheader("مؤشر التقدم")
                    total_days = (end_date_obj - start_date_obj).days if end_date_obj > start_date_obj else 1
                    days_passed = (today - start_date_obj).days if today >= start_date_obj else 0
                    progress = min(1.0, days_passed / total_days if total_days > 0 else 0) * 100
                    
                    fig_gauge = go.Figure(go.Indicator(
                        mode="gauge+number", value=progress,
                        title={'text': f"انقضى {days_passed} من {total_days} يوم"},
                        gauge={'axis': {'range': [None, 100]}, 'bar': {'color': "#2980b9"}}))
                    fig_gauge.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20))
                    st.plotly_chart(fig_gauge, use_container_width=True)

                with col2:
                    st.subheader("مؤشرات الأداء الرئيسية")
                    total_period_minutes = period_logs_df['total_minutes'].sum()
                    total_period_hours = int(total_period_minutes // 60)
                    active_participants = period_logs_df['member_id'].nunique()
                    avg_daily_reading = (total_period_minutes / days_passed / active_participants) if days_passed > 0 and active_participants > 0 else 0
                    total_period_quotes = period_logs_df['submitted_common_quote'].sum() + period_logs_df['submitted_other_quote'].sum()

                    kpi1, kpi2 = st.columns(2)
                    kpi1.metric("⏳ مجموع ساعات القراءة", f"{total_period_hours:,}")
                    kpi2.metric("👥 المشاركون الفعليون", f"{active_participants}")
                    kpi3, kpi4 = st.columns(2)
                    kpi3.metric("✍️ الاقتباسات المرسلة", f"{int(total_period_quotes)}")
                    kpi4.metric("📊 متوسط القراءة اليومي/عضو", f"{avg_daily_reading:.1f} دقيقة")
                st.markdown("---")

                col3, col4 = st.columns(2, gap="large")
                with col3:
                    st.subheader("مجموع ساعات القراءة التراكمي")
                    daily_cumulative_minutes = period_logs_df.groupby('submission_date_dt')['total_minutes'].sum().cumsum().reset_index()
                    daily_cumulative_minutes['total_hours'] = daily_cumulative_minutes['total_minutes'] / 60
                    fig_area = px.area(daily_cumulative_minutes, x='submission_date_dt', y='total_hours', title='', labels={'submission_date_dt': 'تاريخ التحدي', 'total_hours': 'مجموع الساعات'}, color_discrete_sequence=['#2ecc71'])
                    fig_area.update_layout(xaxis_autorange='reversed', yaxis={'side': 'right'})
                    st.plotly_chart(fig_area, use_container_width=True)

                with col4:
                    st.subheader("خريطة الالتزام الحرارية")
                    heatmap_fig = create_activity_heatmap(period_logs_df, start_date_obj, end_date_obj, title_text="")
                    st.plotly_chart(heatmap_fig, use_container_width=True, key="group_heatmap")
                st.markdown("---")

                col5, col6 = st.columns(2, gap="large")
                with col5:
                    st.subheader("ساعات قراءة الأعضاء")
                    hours_chart_df = podium_df.sort_values('hours', ascending=True).tail(10)
                    fig_hours = px.bar(hours_chart_df, x='hours', y='name', orientation='h', title="", labels={'hours': 'مجموع الساعات', 'name': ''}, text='hours', color_discrete_sequence=['#e67e22'])
                    fig_hours.update_traces(texttemplate='%{text:.1f}', textposition='outside')
                    fig_hours.update_layout(yaxis={'side': 'right'}, xaxis_autorange='reversed')
                    st.plotly_chart(fig_hours, use_container_width=True)

                with col6:
                    st.subheader("نقاط الأعضاء")
                    points_chart_df = podium_df.sort_values('points', ascending=True).tail(10)
                    fig_points = px.bar(points_chart_df, x='points', y='name', orientation='h', title="", labels={'points': 'مجموع النقاط', 'name': ''}, text='points', color_discrete_sequence=['#9b59b6'])
                    fig_points.update_traces(textposition='outside')
                    fig_points.update_layout(yaxis={'side': 'right'}, xaxis_autorange='reversed')
                    st.plotly_chart(fig_points, use_container_width=True)

        with tab2:
            if podium_df.empty:
                st.info("لا يوجد مشاركون في هذا التحدي بعد.")
            else:
                member_names = sorted(podium_df['name'].tolist())
                selected_member_name = st.selectbox("اختر قارئاً لعرض بطاقته:", member_names)
                st.markdown("---")

                if selected_member_name:
                    member_data = podium_df[podium_df['name'] == selected_member_name].iloc[0]
                    member_id = member_data['member_id']
                    
                    st.subheader("📊 مؤشرات الأداء")
                    kpi_cols = st.columns(3)
                    kpi_cols[0].metric("⭐ النقاط", f"{int(member_data['points'])}")
                    kpi_cols[1].metric("⏳ ساعات القراءة", f"{member_data['hours']:.1f}")
                    kpi_cols[2].metric("✍️ الاقتباسات", f"{int(member_data['quotes'])}")
                    st.markdown("---")

                    col1, col2 = st.columns(2, gap="large")
                    
                    with col1:
                        st.subheader("🏅 الأوسمة والشارات")
                        member_logs = period_logs_df[period_logs_df['member_id'] == member_id]
                        member_achievements = period_achievements_df[period_achievements_df['member_id'] == member_id] if not period_achievements_df.empty else pd.DataFrame()

                        badges_unlocked = []
                        if member_data['quotes'] > 10: badges_unlocked.append("✍️ **وسام الفيلسوف:** إرسال أكثر من 10 اقتباسات.")
                        if not member_achievements.empty:
                            finish_common_ach = member_achievements[member_achievements['achievement_type'] == 'FINISHED_COMMON_BOOK']
                            if not finish_common_ach.empty:
                                finish_date = pd.to_datetime(finish_common_ach.iloc[0]['achievement_date']).date()
                                if (finish_date - start_date_obj).days <= 7: badges_unlocked.append("🏃‍♂️ **وسام العدّاء:** إنهاء الكتاب في الأسبوع الأول.")
                        if not member_logs.empty:
                            log_dates = sorted(member_logs['submission_date_dt'].unique())
                            if len(log_dates) >= 7:
                                max_streak, current_streak = 0, 0
                                if log_dates:
                                    current_streak = 1; max_streak = 1
                                    for i in range(1, len(log_dates)):
                                        if (log_dates[i] - log_dates[i-1]).days == 1: current_streak += 1
                                        else: max_streak = max(max_streak, current_streak); current_streak = 1
                                    max_streak = max(max_streak, current_streak)
                                if max_streak >= 7: badges_unlocked.append(f"💯 **وسام المثابرة:** القراءة لـ {max_streak} أيام متتالية.")
                        
                        if badges_unlocked:
                            for badge in badges_unlocked: st.success(badge)
                        else: st.info("لا توجد أوسمة بعد.")

                    with col2:
                        st.subheader("🎯 الإنجازات")
                        if not member_achievements.empty:
                            achievement_map = {'FINISHED_COMMON_BOOK': 'إنهاء الكتاب المشترك', 'ATTENDED_DISCUSSION': 'حضور جلسة النقاش', 'FINISHED_OTHER_BOOK': 'إنهاء كتاب آخر'}
                            for _, ach in member_achievements.iterrows(): st.markdown(f"- **{achievement_map.get(ach['achievement_type'], ach['achievement_type'])}**")
                        else: st.info("لا توجد إنجازات بعد.")

                    st.markdown("---")
                    col4, col5 = st.columns(2, gap="large")
                    with col4:
                        st.subheader(f"خريطة التزام: {selected_member_name}")
                        individual_heatmap = create_activity_heatmap(member_logs, start_date_obj, end_date_obj, title_text="")
                        st.plotly_chart(individual_heatmap, use_container_width=True, key="individual_heatmap")
                    with col5:
                        st.subheader("مصادر النقاط")
                        period_rules = selected_challenge_data
                        points_source = {}
                        common_minutes = member_logs['common_book_minutes'].sum()
                        other_minutes = member_logs['other_book_minutes'].sum()
                        if period_rules.get('minutes_per_point_common', 0) > 0: points_source['قراءة الكتاب المشترك'] = (common_minutes // period_rules['minutes_per_point_common'])
                        if period_rules.get('minutes_per_point_other', 0) > 0: points_source['قراءة كتب أخرى'] = (other_minutes // period_rules['minutes_per_point_other'])
                        common_quotes = member_logs['submitted_common_quote'].sum()
                        other_quotes = member_logs['submitted_other_quote'].sum()
                        points_source['اقتباسات (الكتاب المشترك)'] = common_quotes * period_rules.get('quote_common_book_points', 0)
                        points_source['اقتباسات (كتب أخرى)'] = other_quotes * period_rules.get('quote_other_book_points', 0)
                        if not member_achievements.empty:
                            for _, ach in member_achievements.iterrows():
                                ach_type = ach['achievement_type']
                                if ach_type == 'FINISHED_COMMON_BOOK': points_source['إنهاء الكتاب المشترك'] = points_source.get('إنهاء الكتاب المشترك', 0) + period_rules.get('finish_common_book_points', 0)
                                elif ach_type == 'ATTENDED_DISCUSSION': points_source['حضور النقاش'] = points_source.get('حضور النقاش', 0) + period_rules.get('attend_discussion_points', 0)
                                elif ach_type == 'FINISHED_OTHER_BOOK': points_source['إنهاء كتب أخرى'] = points_source.get('إنهاء كتب أخرى', 0) + period_rules.get('finish_other_book_points', 0)
                        points_source_filtered = {k: v for k, v in points_source.items() if v > 0}
                        if points_source_filtered:
                            color_map = {
                                'قراءة الكتاب المشترك': '#3498db', 'قراءة كتب أخرى': '#f1c40f',
                                'اقتباسات (الكتاب المشترك)': '#2ecc71', 'اقتباسات (كتب أخرى)': '#e67e22',
                                'إنهاء الكتاب المشترك': '#9b59b6', 'حضور النقاش': '#e74c3c',
                                'إنهاء كتب أخرى': '#1abc9c'
                            }
                            chart_labels = list(points_source_filtered.keys())
                            chart_colors = [color_map.get(label, '#bdc3c7') for label in chart_labels]

                            fig_donut = go.Figure(data=[go.Pie(
                                labels=chart_labels, values=list(points_source_filtered.values()), 
                                hole=.5, textinfo='percent', insidetextorientation='radial',
                                marker_colors=chart_colors
                            )])
                            fig_donut.update_layout(
                                showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                                margin=dict(t=20, b=50, l=20, r=20)
                            )
                            st.plotly_chart(fig_donut, use_container_width=True)
                        else: st.info("لا توجد نقاط مسجلة لعرض مصادرها.")
        
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
                        
                        challenge_kpis = {
                            "⏳ مجموع ساعات القراءة": f"{total_period_hours:,}",
                            "👥 المشاركون الفعليون": f"{active_participants}",
                            "✍️ الاقتباسات المرسلة": f"{int(total_period_quotes)}",
                            "📊 متوسط القراءة اليومي/عضو": f"{avg_daily_reading:.1f} د"
                        }

                        challenge_data_for_pdf = {
                            "title": selected_challenge_data.get('book_title', ''),
                            "author": selected_challenge_data.get('book_author', ''),
                            "period": challenge_period_str,
                            "duration": challenge_duration,
                            "all_participants": all_participants_names,
                            "finishers": finishers_names,
                            "attendees": attendees_names,
                            "kpis": challenge_kpis,
                            "fig_area": fig_area,
                            "fig_hours": fig_hours,
                            "fig_points": fig_points
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


elif page == "⚙️ الإدارة والإعدادات":
    st.header("⚙️ الإدارة والإعدادات")
    
    admin_tab1, admin_tab2, admin_tab3 = st.tabs(["إدارة المشاركين والتحديات", "إعدادات النقاط والروابط", "📝 محرر السجلات"])

    with admin_tab1:
        st.subheader("👥 إدارة المشاركين")
        
        with st.form("add_member_form"):
            new_member_name = st.text_input("اسم العضو الجديد")
            submitted = st.form_submit_button("➕ إضافة عضو جديد")
            if submitted and new_member_name:
                with st.spinner(f"جاري إضافة {new_member_name}..."):
                    db.add_members(user_id, [new_member_name.strip()])
                    st.success(f"تمت إضافة العضو '{new_member_name}' بنجاح.")
                    
                    updated_members_df = db.get_subcollection_as_df(user_id, 'members')
                    active_member_names = updated_members_df[updated_members_df['is_active'] == True]['name'].tolist()
                    form_id = user_settings.get('form_id')
                    question_id = user_settings.get('member_question_id')
                    if update_form_members(forms_service, form_id, question_id, active_member_names):
                        st.info("✅ تم تحديث قائمة الأعضاء في نموذج جوجل بنجاح.")
                    
                    time.sleep(2)
                    st.rerun()

        st.divider()

        active_members_df = members_df[members_df['is_active'] == True] if not members_df.empty else pd.DataFrame()
        inactive_members_df = members_df[members_df['is_active'] == False] if not members_df.empty else pd.DataFrame()

        st.subheader(f"✅ الأعضاء النشطون ({len(active_members_df)})")
        if not active_members_df.empty:
            for index, member in active_members_df.iterrows():
                col1, col2 = st.columns([4, 1])
                col1.write(member['name'])
                member_id = member['members_id'] 
                if col2.button("🚫 تعطيل", key=f"deactivate_{member_id}", use_container_width=True):
                    with st.spinner(f"جاري تعطيل {member['name']}..."):
                        db.set_member_status(user_id, member_id, False)
                        
                        current_active_names = active_members_df[active_members_df['members_id'] != member_id]['name'].tolist()
                        form_id = user_settings.get('form_id')
                        question_id = user_settings.get('member_question_id')
                        update_form_members(forms_service, form_id, question_id, current_active_names)
                        
                        st.success(f"تم تعطيل {member['name']} وإزالته من نموذج التسجيل.")
                        st.rerun()
        else:
            st.info("لا يوجد أعضاء نشطون حالياً.")

        st.subheader(f"🗂️ أرشيف الأعضاء ({len(inactive_members_df)})")
        if not inactive_members_df.empty:
            for index, member in inactive_members_df.iterrows():
                col1, col2 = st.columns([4, 1])
                col1.write(f"_{member['name']}_")
                member_id = member['members_id']
                if col2.button("🔄 إعادة تنشيط", key=f"reactivate_{member_id}", use_container_width=True):
                     with st.spinner(f"جاري إعادة تنشيط {member['name']}..."):
                        db.set_member_status(user_id, member_id, True)
                        
                        final_active_names = active_members_df['name'].tolist() + [member['name']]
                        form_id = user_settings.get('form_id')
                        question_id = user_settings.get('member_question_id')
                        update_form_members(forms_service, form_id, question_id, final_active_names)

                        st.success(f"تم إعادة تنشيط {member['name']} وإضافته إلى نموذج التسجيل.")
                        st.rerun()
        else:
            st.info("لا يوجد أعضاء في الأرشيف.")

        st.divider()

        st.subheader("📅 إدارة تحديات القراءة")
        today_str = str(date.today())
        active_period_id = None
        if not periods_df.empty:
            active_periods = periods_df[(periods_df['start_date'] <= today_str) & (periods_df['end_date'] >= today_str)]
            if not active_periods.empty:
                active_period_id = active_periods.iloc[0]['periods_id']
                
        # عرض القائمة إذا كانت هناك تحديات
        if not periods_df.empty:
            cols = st.columns((4, 2, 2, 2, 1, 1))
            headers = ["عنوان الكتاب", "المؤلف", "تاريخ البداية", "تاريخ النهاية", "معلومات", "إجراء"]
            for col, header in zip(cols, headers):
                col.write(f"**{header}**")
                
            for index, period in periods_df.iterrows():
                col1, col2, col3, col4, col5, col6 = st.columns((4, 2, 2, 2, 1, 1))
                col1.write(period['book_title'])
                col2.write(period['book_author'])
                col3.write(period['start_date'])
                col4.write(period['end_date'])
                period_id = period['periods_id']

                if col5.button("ℹ️", key=f"info_{period_id}", help="عرض نظام النقاط لهذا التحدي"):
                    st.session_state.challenge_to_show_rules = period.to_dict()
                    st.rerun()

                is_active = period_id == active_period_id
                delete_button_disabled = bool(is_active)
                delete_button_help = "لا يمكن حذف التحدي النشط حالياً." if is_active else None
                if col6.button("🗑️", key=f"delete_{period_id}", disabled=delete_button_disabled, help=delete_button_help, use_container_width=True):
                    st.session_state['challenge_to_delete'] = period_id
                    st.session_state['delete_confirmation_phrase'] = f"أوافق على حذف {period['book_title']}"
                    st.rerun()
        # عرض رسالة إذا لم تكن هناك تحديات
        else:
            st.info("لا توجد تحديات لعرضها.")

        # --- منطق النافذة المنبثقة لعرض القوانين (يجب أن يكون خارج كتلة if/else) ---
        if 'challenge_to_show_rules' in st.session_state:
            @st.dialog("نظام النقاط المطبق على التحدي")
            def show_challenge_rules_dialog():
                rules = st.session_state.challenge_to_show_rules
                st.subheader(f"كتاب: {rules.get('book_title', 'N/A')}")
                
                st.markdown(f"""
                - **دقائق قراءة الكتاب المشترك لكل نقطة:** `{rules.get('minutes_per_point_common', 'N/A')}`
                - **دقائق قراءة كتاب آخر لكل نقطة:** `{rules.get('minutes_per_point_other', 'N/A')}`
                - **نقاط إنهاء الكتاب المشترك:** `{rules.get('finish_common_book_points', 'N/A')}`
                - **نقاط إنهاء كتاب آخر:** `{rules.get('finish_other_book_points', 'N/A')}`
                - **نقاط اقتباس الكتاب المشترك:** `{rules.get('quote_common_book_points', 'N/A')}`
                - **نقاط اقتباس كتاب آخر:** `{rules.get('quote_other_book_points', 'N/A')}`
                - **نقاط حضور جلسة النقاش:** `{rules.get('attend_discussion_points', 'N/A')}`
                """)
                
                if st.button("إغلاق"):
                    del st.session_state.challenge_to_show_rules
                    st.rerun()
                    
            show_challenge_rules_dialog()
        
        with st.expander("اضغط هنا لإضافة تحدي جديد"):
            with st.form("add_new_challenge_details_form"):
                st.write("**تفاصيل الكتاب والتحدي**")
                new_title = st.text_input("عنوان الكتاب الجديد", key="new_chal_title")
                new_author = st.text_input("مؤلف الكتاب الجديد", key="new_chal_author")
                new_year = st.number_input("سنة نشر الكتاب الجديد", value=datetime.now().year, step=1, key="new_chal_year")
                
                last_end_date = pd.to_datetime(periods_df['end_date'].max()).date() if not periods_df.empty else date.today() - timedelta(days=1)
                suggested_start = last_end_date + timedelta(days=1)
                new_start = st.date_input("تاريخ بداية التحدي الجديد", value=suggested_start, key="new_chal_start")
                new_end = st.date_input("تاريخ نهاية التحدي الجديد", value=suggested_start + timedelta(days=30), key="new_chal_end")

                if st.form_submit_button("متابعة لاختيار نظام النقاط"):
                    if new_start <= last_end_date:
                        st.error(f"⛔ التواريخ متداخلة: يرجى اختيار تاريخ بداية بعد {last_end_date}.")
                    elif not new_title or not new_author:
                        st.error("✏️ بيانات غير مكتملة: يرجى إدخال عنوان الكتاب واسم المؤلف للمتابعة.")
                    elif new_start >= new_end:
                        st.error("🗓️ خطأ في التواريخ: تاريخ نهاية التحدي يجب أن يكون بعد تاريخ بدايته.")
                    else:
                        # حفظ البيانات مؤقتاً في الـ session state لعرضها في النافذة المنبثقة
                        st.session_state.new_challenge_data = {
                            'book_info': {'title': new_title, 'author': new_author, 'year': new_year},
                            'challenge_info': {'start_date': str(new_start), 'end_date': str(new_end)}
                        }
                        st.session_state.show_rules_choice = True
                        st.rerun()

        # --- منطق النوافذ المنبثقة لاختيار وتخصيص القوانين ---
        if 'show_rules_choice' in st.session_state and st.session_state.show_rules_choice:
            @st.dialog("اختر نظام النقاط للتحدي")
            def show_rules_choice_dialog():
                st.write(f"اختر نظام النقاط الذي تريد تطبيقه على تحدي كتاب **'{st.session_state.new_challenge_data['book_info']['title']}'**.")
                
                if st.button("📈 استخدام النظام الافتراضي", use_container_width=True):
                    default_rules = db.load_user_global_rules(user_id)
                    success, message = db.add_book_and_challenge(
                        user_id,
                        st.session_state.new_challenge_data['book_info'],
                        st.session_state.new_challenge_data['challenge_info'],
                        default_rules
                    )
                    if success:
                        st.success(f"✅ {message}")
                    else:
                        st.error(f"❌ {message}")
                    
                    del st.session_state.show_rules_choice
                    del st.session_state.new_challenge_data
                    st.rerun()

                if st.button("🛠️ تخصيص القوانين لهذا التحدي", type="primary", use_container_width=True):
                    st.session_state.show_custom_rules_form = True
                    del st.session_state.show_rules_choice
                    st.rerun()

            show_rules_choice_dialog()

        if 'show_custom_rules_form' in st.session_state and st.session_state.show_custom_rules_form:
            @st.dialog("تخصيص قوانين التحدي")
            def show_custom_rules_dialog():
                default_settings = db.load_user_global_rules(user_id)
                with st.form("custom_rules_form"):
                    st.info("أنت الآن تقوم بتعيين قوانين خاصة لهذا التحدي فقط.")
                    c1, c2 = st.columns(2)
                    rules = {}
                    rules['minutes_per_point_common'] = c1.number_input("دقائق قراءة الكتاب المشترك لكل نقطة:", value=default_settings['minutes_per_point_common'], min_value=0)
                    rules['minutes_per_point_other'] = c2.number_input("دقائق قراءة كتاب آخر لكل نقطة:", value=default_settings['minutes_per_point_other'], min_value=0)
                    rules['quote_common_book_points'] = c1.number_input("نقاط اقتباس الكتاب المشترك:", value=default_settings['quote_common_book_points'], min_value=0)
                    rules['quote_other_book_points'] = c2.number_input("نقاط اقتباس كتاب آخر:", value=default_settings['quote_other_book_points'], min_value=0)
                    rules['finish_common_book_points'] = c1.number_input("نقاط إنهاء الكتاب المشترك:", value=default_settings['finish_common_book_points'], min_value=0)
                    rules['finish_other_book_points'] = c2.number_input("نقاط إنهاء كتاب آخر:", value=default_settings['finish_other_book_points'], min_value=0)
                    rules['attend_discussion_points'] = st.number_input("نقاط حضور جلسة النقاش:", value=default_settings['attend_discussion_points'], min_value=0)
                    
                    if st.form_submit_button("حفظ التحدي بالقوانين المخصصة"):
                        success, message = db.add_book_and_challenge(
                            user_id,
                            st.session_state.new_challenge_data['book_info'],
                            st.session_state.new_challenge_data['challenge_info'],
                            rules
                        )
                        if success:
                            st.success(f"✅ {message}")
                        else:
                            st.error(f"❌ {message}")

                        del st.session_state.show_custom_rules_form
                        del st.session_state.new_challenge_data
                        st.rerun()

            show_custom_rules_dialog()
        
        if 'challenge_to_delete' in st.session_state:
            @st.dialog("🚫 تأكيد الحذف النهائي")
            def show_challenge_delete_dialog():
                st.warning("☢️ إجراء لا يمكن التراجع عنه: أنت على وشك حذف التحدي وكل ما يتعلق به من إنجازات.")
                confirmation_phrase = st.session_state['delete_confirmation_phrase']
                st.code(confirmation_phrase)
                user_input = st.text_input("اكتب عبارة التأكيد هنا:", key="challenge_delete_input")
                if st.button("❌ حذف التحدي نهائياً", disabled=(user_input != confirmation_phrase), type="primary"):
                    if db.delete_challenge(user_id, st.session_state['challenge_to_delete']):
                        del st.session_state['challenge_to_delete']
                        st.success("🗑️ اكتمل الحذف.")
                        st.rerun()
                if st.button("إلغاء"):
                    del st.session_state['challenge_to_delete']
                    st.rerun()
            show_challenge_delete_dialog()

    with admin_tab2:
        st.subheader("🔗 رابط المشاركة")
        st.info("هذا هو الرابط الذي يمكنك مشاركته مع أعضاء الفريق لتسجيل قراءاتهم اليومية.")
        if form_url:
            st.code(form_url)
        else:
            st.warning("لم يتم إنشاء رابط النموذج بعد. يرجى إكمال خطوات الإعداد أولاً.")
        
        st.divider()

        st.subheader("🎯 نظام النقاط الافتراضي")
        st.info("هذه هي القوانين الافتراضية التي سيتم تطبيقها على التحديات الجديدة.")
        settings = db.load_user_global_rules(user_id)
        if settings:
            with st.form("settings_form"):
                c1, c2 = st.columns(2)
                s_m_common = c1.number_input("دقائق قراءة الكتاب المشترك لكل نقطة:", value=settings.get('minutes_per_point_common', 10), min_value=0)
                s_m_other = c2.number_input("دقائق قراءة كتاب آخر لكل نقطة:", value=settings.get('minutes_per_point_other', 5), min_value=0)
                s_q_common = c1.number_input("نقاط اقتباس الكتاب المشترك:", value=settings.get('quote_common_book_points', 3), min_value=0)
                s_q_other = c2.number_input("نقاط اقتباس كتاب آخر:", value=settings.get('quote_other_book_points', 1), min_value=0)
                s_f_common = c1.number_input("نقاط إنهاء الكتاب المشترك:", value=settings.get('finish_common_book_points', 50), min_value=0)
                s_f_other = c2.number_input("نقاط إنهاء كتاب آخر:", value=settings.get('finish_other_book_points', 25), min_value=0)
                s_a_disc = st.number_input("نقاط حضور جلسة النقاش:", value=settings.get('attend_discussion_points', 25), min_value=0)
                
                if st.form_submit_button("حفظ الإعدادات الافتراضية", use_container_width=True):
                    new_settings = {
                        "minutes_per_point_common": s_m_common, "minutes_per_point_other": s_m_other,
                        "quote_common_book_points": s_q_common, "quote_other_book_points": s_q_other,
                        "finish_common_book_points": s_f_common, "finish_other_book_points": s_f_other,
                        "attend_discussion_points": s_a_disc
                    }
                    if db.update_user_global_rules(user_id, new_settings):
                        st.success("👍 تم حفظ التغييرات! تم تحديث نظام النقاط الافتراضي بنجاح.")
                    else:
                        st.error("حدث خطأ أثناء تحديث الإعدادات.")
    
    with admin_tab3:
        # --- التعديل هنا: إعادة تفعيل محرر السجلات بالكامل ---
        st.header("📝 محرر السجلات الذكي")
        st.info("لضمان تعديل أحدث البيانات، يرجى الضغط على الزر أدناه لسحب السجلات مباشرة من Google Sheet قبل البدء بالتعديل.")

        if st.button("⬇️ تحميل أحدث السجلات للتعديل", use_container_width=True):
            with st.spinner("جاري سحب أحدث البيانات من Google Sheet..."):
                try:
                    spreadsheet = gc.open_by_url(spreadsheet_url)
                    worksheet = spreadsheet.worksheet("Form Responses 1")
                    sheet_data = worksheet.get_all_records()
                    
                    if not sheet_data:
                        st.warning("جدول البيانات فارغ. لا توجد سجلات لعرضها.")
                        st.stop()

                    df = pd.DataFrame(sheet_data)
                    df['sheet_row_index'] = df.index + 2

                    ACHIEVEMENT_OPTIONS = {
                        'ach_finish_common': 'أنهيت الكتاب المشترك',
                        'ach_finish_other': 'أنهيت كتاباً آخر',
                        'ach_attend_discussion': 'حضرت جلسة النقاش'
                    }
                    QUOTE_OPTIONS = {
                        'quote_common': 'أرسلت اقتباساً من الكتاب المشترك',
                        'quote_other': 'أرسلت اقتباساً من كتاب آخر'
                    }

                    achievements_col_name = next((col for col in df.columns if 'إنجازات الكتب والنقاش' in col), None)
                    quotes_col_name = next((col for col in df.columns if 'الاقتباسات التي أرسلتها' in col), None)

                    if achievements_col_name:
                        df[achievements_col_name] = df[achievements_col_name].astype(str)
                        for key, text in ACHIEVEMENT_OPTIONS.items():
                            df[key] = df[achievements_col_name].str.contains(text, na=False)
                    
                    if quotes_col_name:
                        df[quotes_col_name] = df[quotes_col_name].astype(str)
                        for key, text in QUOTE_OPTIONS.items():
                            df[key] = df[quotes_col_name].str.contains(text, na=False)
                    
                    st.session_state.editor_data = df
                    st.session_state.original_editor_data = df.copy()
                    st.rerun()

                except Exception as e:
                    st.error(f"حدث خطأ أثناء سحب البيانات من Google Sheet: {e}")

        if 'editor_data' in st.session_state:
            st.success("تم تحميل البيانات بنجاح. يمكنك الآن تعديل السجلات أدناه.")
            
            original_df = st.session_state.original_editor_data
            
            achievements_col_name = next((col for col in original_df.columns if 'إنجازات الكتب والنقاش' in col), "إنجازات الكتب والنقاش (اختر فقط عند حدوثه لأول مرة)")
            quotes_col_name = next((col for col in original_df.columns if 'الاقتباسات التي أرسلتها' in col), "ما هي الاقتباسات التي أرسلتها اليوم؟ (اختياري)")
            common_minutes_col_name = next((col for col in original_df.columns if 'مدة قراءة الكتاب المشترك' in col), "مدة قراءة الكتاب المشترك (اختياري)")
            other_minutes_col_name = next((col for col in original_df.columns if 'مدة قراءة كتاب آخر' in col), "مدة قراءة كتاب آخر (اختياري)")
            date_col_name = "تاريخ القراءة"
            name_col_name = "اسمك"
            timestamp_col_name = "Timestamp"

            edited_df = st.data_editor(
                st.session_state.editor_data,
                key="data_editor_final",
                column_config={
                    achievements_col_name: None, quotes_col_name: None,
                    'ach_finish_common': st.column_config.CheckboxColumn("أنهى المشترك؟"),
                    'ach_finish_other': st.column_config.CheckboxColumn("أنهى آخر؟"),
                    'ach_attend_discussion': st.column_config.CheckboxColumn("حضر النقاش؟"),
                    'quote_common': st.column_config.CheckboxColumn("اقتباس مشترك؟"),
                    'quote_other': st.column_config.CheckboxColumn("اقتباس آخر؟"),
                    common_minutes_col_name: st.column_config.TextColumn("دقائق (مشترك)"),
                    other_minutes_col_name: st.column_config.TextColumn("دقائق (آخر)"),
                    date_col_name: st.column_config.TextColumn("تاريخ القراءة"),
                    name_col_name: st.column_config.TextColumn("الاسم", disabled=True),
                    timestamp_col_name: st.column_config.TextColumn("ختم الوقت", disabled=True),
                    'sheet_row_index': None,
                },
                use_container_width=True, height=500, hide_index=True
            )

            if st.button("💾 حفظ التعديلات في Google Sheet", use_container_width=True, type="primary"):
                with st.spinner("جاري حفظ التغييرات..."):
                    try:
                        spreadsheet = gc.open_by_url(spreadsheet_url)
                        worksheet = spreadsheet.worksheet("Form Responses 1")
                        sheet_headers = worksheet.row_values(1)

                        comparison_cols = list(edited_df.columns)
                        if 'sheet_row_index' in comparison_cols:
                            comparison_cols.remove('sheet_row_index')
                        
                        # تحويل كل الأعمدة للمقارنة إلى نص لتجنب أخطاء الأنواع
                        original_for_comp = original_df[comparison_cols].astype(str)
                        edited_for_comp = edited_df[comparison_cols].astype(str)
                        
                        changed_rows_mask = (original_for_comp != edited_for_comp).any(axis=1)
                        changes = edited_df[changed_rows_mask]
                        
                        if changes.empty:
                            st.info("لم يتم العثور على أي تغييرات لحفظها.")
                        else:
                            batch_updates = []
                            for idx in changes.index:
                                edited_row = changes.loc[idx]
                                sheet_row_to_update = edited_row['sheet_row_index']
                                
                                ACH_OPTIONS = {'ach_finish_common': 'أنهيت الكتاب المشترك', 'ach_finish_other': 'أنهيت كتاباً آخر', 'ach_attend_discussion': 'حضرت جلسة النقاش'}
                                QUOTE_OPTIONS = {'quote_common': 'أرسلت اقتباساً من الكتاب المشترك', 'quote_other': 'أرسلت اقتباساً من كتاب آخر'}

                                new_ach_list = [text for key, text in ACH_OPTIONS.items() if edited_row[key]]
                                new_ach_str = ", ".join(new_ach_list)
                                
                                new_quote_list = [text for key, text in QUOTE_OPTIONS.items() if edited_row[key]]
                                new_quote_str = ", ".join(new_quote_list)

                                # تحديث الأعمدة البسيطة
                                for col_name in [date_col_name, common_minutes_col_name, other_minutes_col_name]:
                                    if col_name in sheet_headers:
                                        col_idx = sheet_headers.index(col_name) + 1
                                        batch_updates.append({'range': f'{gspread.utils.rowcol_to_a1(sheet_row_to_update, col_idx)}', 'values': [[str(edited_row[col_name])]]})
                                
                                # تحديث أعمدة الاختيار المتعدد
                                if achievements_col_name in sheet_headers:
                                    ach_col_idx = sheet_headers.index(achievements_col_name) + 1
                                    batch_updates.append({'range': f'{gspread.utils.rowcol_to_a1(sheet_row_to_update, ach_col_idx)}', 'values': [[new_ach_str]]})
                                
                                if quotes_col_name in sheet_headers:
                                    quote_col_idx = sheet_headers.index(quotes_col_name) + 1
                                    batch_updates.append({'range': f'{gspread.utils.rowcol_to_a1(sheet_row_to_update, quote_col_idx)}', 'values': [[new_quote_str]]})
                            
                            if batch_updates:
                                worksheet.batch_update(batch_updates)
                                st.success(f"✅ تم تحديث {len(changes)} سجل بنجاح في Google Sheet.")
                                st.info("سيتم الآن إعادة مزامنة التطبيق بالكامل لتعكس التغييرات.")
                                with st.spinner("جاري المزامنة الكاملة..."):
                                    run_data_update(gc, user_id)
                                st.success("🎉 اكتملت المزامنة!")
                            else:
                                st.info("لم يتم العثور على أي تغييرات لحفظها.")
                        
                        del st.session_state.editor_data
                        if 'original_editor_data' in st.session_state:
                            del st.session_state.original_editor_data
                        st.rerun()

                    except Exception as e:
                        st.error(f"حدث خطأ فادح أثناء عملية الحفظ: {e}")
