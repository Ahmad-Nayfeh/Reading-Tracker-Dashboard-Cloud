import streamlit as st
import pandas as pd
from datetime import date, timedelta, datetime
import db_manager as db
import auth_manager # <-- استيراد مدير المصادقة
from main import run_data_update
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import gspread
import time

st.set_page_config(
    page_title="الإدارة والإعدادات",
    page_icon="⚙️",
    layout="wide"
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


# --- 1. UNIFIED AUTHENTICATION BLOCK ---
# This is the new, robust authentication block that will be used on all pages.
creds = auth_manager.authenticate()
user_id = st.session_state.get('user_id')

# If authentication fails, auth_manager would have already stopped the app.
# But as a safeguard:
if not creds or not user_id:
    st.error("مصادقة المستخدم مطلوبة. يرجى العودة إلى الصفحة الرئيسية وتسجيل الدخول.")
    st.stop()
# -----------------------------------------


# --- Helper function to update Google Form ---
def update_form_members(forms_service, form_id, question_id, active_member_names):
    if not form_id or not question_id:
        st.error("لم يتم العثور على معرّف النموذج أو معرّف سؤال الأعضاء في الإعدادات.")
        return False
    
    # Ensure names are sorted for consistency
    sorted_names = sorted(active_member_names)
    
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
                                    "options": [{"value": name} for name in sorted_names]
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


# Initialize Google clients once and cache them
gc = auth_manager.get_gspread_client(user_id, creds)
forms_service = build('forms', 'v1', credentials=creds)

# --- Data Loading (FIXED) ---
@st.cache_data(ttl=300)
def load_management_data(user_id):
    members_df = db.get_subcollection_as_df(user_id, 'members')
    periods_df = db.get_subcollection_as_df(user_id, 'periods')
    books_df = db.get_subcollection_as_df(user_id, 'books') # Fetch books data
    user_settings = db.get_user_settings(user_id)

    # Merge book info into periods_df
    if not periods_df.empty and not books_df.empty:
        books_df.rename(columns={'title': 'book_title', 'author': 'book_author', 'publication_year': 'book_year'}, inplace=True)
        periods_df = pd.merge(periods_df, books_df, left_on='common_book_id', right_on='books_id', how='left')

    return members_df, periods_df, user_settings

members_df, periods_df, user_settings = load_management_data(user_id)

# --- Page Rendering ---
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
                
                # Update form immediately
                updated_members_df = db.get_subcollection_as_df(user_id, 'members')
                active_member_names = updated_members_df[updated_members_df['is_active'] == True]['name'].tolist()
                form_id = user_settings.get('form_id')
                question_id = user_settings.get('member_question_id')
                if update_form_members(forms_service, form_id, question_id, active_member_names):
                    st.info("✅ تم تحديث قائمة الأعضاء في نموذج جوجل بنجاح.")
                
                # Clear cache and rerun
                st.cache_data.clear()
                time.sleep(1)
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
                    st.cache_data.clear()
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
                    st.cache_data.clear()
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
            
    if not periods_df.empty:
        cols = st.columns((4, 2, 2, 2, 1, 1))
        headers = ["عنوان الكتاب", "المؤلف", "تاريخ البداية", "تاريخ النهاية", "معلومات", "إجراء"]
        for col, header in zip(cols, headers):
            col.write(f"**{header}**")
            
        for index, period in periods_df.iterrows():
            col1, col2, col3, col4, col5, col6 = st.columns((4, 2, 2, 2, 1, 1))
            # Use .get() for safety against missing data after the merge
            col1.write(period.get('book_title', 'غير متوفر'))
            col2.write(period.get('book_author', 'غير متوفر'))
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
                st.session_state['delete_confirmation_phrase'] = f"أوافق على حذف {period.get('book_title', 'هذا التحدي')}"
                st.rerun()
    else:
        st.info("لا توجد تحديات لعرضها.")

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
                    st.session_state.new_challenge_data = {
                        'book_info': {'title': new_title, 'author': new_author, 'year': new_year},
                        'challenge_info': {'start_date': str(new_start), 'end_date': str(new_end)}
                    }
                    st.session_state.show_rules_choice = True
                    st.rerun()

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
                if success: st.success(f"✅ {message}")
                else: st.error(f"❌ {message}")
                del st.session_state.show_rules_choice
                del st.session_state.new_challenge_data
                st.cache_data.clear()
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
                    if success: st.success(f"✅ {message}")
                    else: st.error(f"❌ {message}")
                    del st.session_state.show_custom_rules_form
                    del st.session_state.new_challenge_data
                    st.cache_data.clear()
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
                    st.cache_data.clear()
                    st.rerun()
            if st.button("إلغاء"):
                del st.session_state['challenge_to_delete']
                st.rerun()
        show_challenge_delete_dialog()

with admin_tab2:
    st.subheader("🔗 رابط المشاركة")
    st.info("هذا هو الرابط الذي يمكنك مشاركته مع أعضاء الفريق لتسجيل قراءاتهم اليومية.")
    form_url = user_settings.get("form_url")
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
    st.header("📝 محرر السجلات الذكي")
    st.info("لضمان تعديل أحدث البيانات، يرجى الضغط على الزر أدناه لسحب السجلات مباشرة من Google Sheet قبل البدء بالتعديل.")
    spreadsheet_url = user_settings.get("spreadsheet_url")

    if st.button("⬇️ تحميل أحدث السجلات للتعديل", use_container_width=True):
        if not spreadsheet_url:
            st.error("لم يتم تحديد رابط جدول البيانات في الإعدادات. يرجى إكمال الإعداد أولاً.")
        else:
            with st.spinner("جاري سحب أحدث البيانات من Google Sheet..."):
                try:
                    spreadsheet = gc.open_by_url(spreadsheet_url)
                    worksheet = spreadsheet.worksheet("Form Responses 1")
                    sheet_data = worksheet.get_all_records()

                    if not sheet_data:
                        st.warning("جدول البيانات فارغ. لا توجد سجلات لعرضها.")
                    else:
                        df = pd.DataFrame(sheet_data)
                        df['sheet_row_index'] = df.index + 2

                        ACHIEVEMENT_OPTIONS = {'ach_finish_common': 'أنهيت الكتاب المشترك', 'ach_finish_other': 'أنهيت كتاباً آخر', 'ach_attend_discussion': 'حضرت جلسة النقاش'}
                        QUOTE_OPTIONS = {'quote_common': 'أرسلت اقتباساً من الكتاب المشترك', 'quote_other': 'أرسلت اقتباساً من كتاب آخر'}
                        
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

                except gspread.exceptions.WorksheetNotFound:
                    st.error("❌ لم يتم العثور على ورقة 'Form Responses 1'. يرجى التأكد من أنك قمت بإعادة تسمية ورقة الردود إلى هذا الاسم بالضبط.")
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

                            new_ach_list = [text for key, text in ACH_OPTIONS.items() if edited_row.get(key)]
                            new_ach_str = ", ".join(new_ach_list)
                            
                            new_quote_list = [text for key, text in QUOTE_OPTIONS.items() if edited_row.get(key)]
                            new_quote_str = ", ".join(new_quote_list)

                            for col_name in [date_col_name, common_minutes_col_name, other_minutes_col_name]:
                                if col_name in sheet_headers:
                                    col_idx = sheet_headers.index(col_name) + 1
                                    batch_updates.append({'range': f'{gspread.utils.rowcol_to_a1(sheet_row_to_update, col_idx)}', 'values': [[str(edited_row[col_name])]]})
                            
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
