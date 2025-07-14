import pandas as pd
from firebase_config import db # استيراد عميل قاعدة البيانات المهيأ

# --- بنية قاعدة البيانات في Firestore ---
# users (collection)
#  └── {user_id} (document) - يمثل مساحة عمل كل مشرف
#      ├── settings (document)
#      ├── global_rules (document)
#      ├── members (subcollection)
#      ├── books (subcollection)
#      ├── periods (subcollection)
#      ├── logs (subcollection)
#      ├── achievements (subcollection)
#      └── member_stats (subcollection)
# -------------------------------------------------


def check_user_exists(user_id: str):
    """
    يتحقق مما إذا كان للمستخدم مساحة عمل موجودة في Firestore.
    """
    user_doc_ref = db.collection('users').document(user_id)
    return user_doc_ref.get().exists

def create_new_user_workspace(user_id: str, user_email: str):
    """
    ينشئ مساحة عمل جديدة لمشرف جديد عند تسجيل الدخول لأول مرة.
    """
    user_doc_ref = db.collection('users').document(user_id)
    
    user_doc_ref.set({
        'email': user_email,
        'created_at': pd.Timestamp.now()
    })
    
    user_doc_ref.collection('settings').document('config').set({
        'spreadsheet_url': '',
        'form_url': '',
        'form_id': '',
        'member_question_id': '',
        'refresh_token': None
    })
    
    user_doc_ref.collection('global_rules').document('rules').set({
        'minutes_per_point_common': 10,
        'minutes_per_point_other': 5,
        'finish_common_book_points': 50,
        'finish_other_book_points': 25,
        'quote_common_book_points': 3,
        'quote_other_book_points': 1,
        'attend_discussion_points': 25
    })

# --- دوال الإعدادات الخاصة بكل مستخدم ---

def set_user_setting(user_id: str, key: str, value: str):
    """
    يحفظ أو يحدّث إعدادًا معينًا للمستخدم المحدد.
    """
    settings_ref = db.collection('users').document(user_id).collection('settings').document('config')
    settings_ref.update({key: value})

def get_user_settings(user_id: str):
    """
    يسترجع جميع إعدادات المستخدم المحدد.
    """
    settings_ref = db.collection('users').document(user_id).collection('settings').document('config')
    doc = settings_ref.get()
    return doc.to_dict() if doc.exists else {}

def load_user_global_rules(user_id: str):
    """
    يقوم بتحميل نظام النقاط الافتراضي للمستخدم المحدد.
    """
    rules_ref = db.collection('users').document(user_id).collection('global_rules').document('rules')
    doc = rules_ref.get()
    return doc.to_dict() if doc.exists else None

def update_user_global_rules(user_id: str, settings_dict: dict):
    """
    يحدّث نظام النقاط الافتراضي للمستخدم المحدد.
    """
    rules_ref = db.collection('users').document(user_id).collection('global_rules').document('rules')
    rules_ref.set(settings_dict)
    return True

# --- دوال القراءة (Read Functions) ---

def get_subcollection_as_df(user_id: str, collection_name: str):
    """
    يجلب مجموعة فرعية كاملة للمستخدم المحدد ويعيدها كـ Pandas DataFrame.
    """
    collection_ref = db.collection('users').document(user_id).collection(collection_name)
    docs = collection_ref.stream()
    data = []
    for doc in docs:
        doc_data = doc.to_dict()
        doc_data[f'{collection_name}_id'] = doc.id
        data.append(doc_data)
    return pd.DataFrame(data)

def get_all_data_for_stats(user_id: str):
    """
    يجلب جميع البيانات اللازمة لمحرك الحسابات لمستخدم معين.
    """
    members_df = get_subcollection_as_df(user_id, 'members')
    logs_df = get_subcollection_as_df(user_id, 'logs')
    achievements_df = get_subcollection_as_df(user_id, 'achievements')
    periods_df = get_subcollection_as_df(user_id, 'periods')
    books_df = get_subcollection_as_df(user_id, 'books')

    if not periods_df.empty and not books_df.empty:
        books_df.rename(columns={'title': 'book_title', 'author': 'book_author', 'publication_year': 'book_year'}, inplace=True)
        periods_df = pd.merge(periods_df, books_df, left_on='common_book_id', right_on='books_id', how='left')
    
    return {
        "members": members_df.to_dict('records'),
        "logs": logs_df.to_dict('records'),
        "achievements": achievements_df.to_dict('records'),
        "periods": periods_df.to_dict('records')
    }

def has_achievement(user_id: str, member_id: str, achievement_type: str, period_id: str):
    """
    يتحقق مما إذا كان لدى العضو إنجاز معين في تحدي معين.
    """
    achievements_ref = db.collection('users').document(user_id).collection('achievements')
    query = achievements_ref.where('member_id', '==', member_id)\
                            .where('achievement_type', '==', achievement_type)\
                            .where('period_id', '==', period_id)
    return len(list(query.stream())) > 0

# --- دوال الكتابة والتحديث (Write/Update Functions) ---

def add_members(user_id: str, names_list: list):
    """
    يضيف قائمة من الأعضاء الجدد إلى مساحة عمل المستخدم.
    """
    members_ref = db.collection('users').document(user_id).collection('members')
    for name in names_list:
        members_ref.add({'name': name, 'is_active': True})

def set_member_status(user_id: str, member_id: str, is_active: bool):
    """
    يضبط حالة العضو (نشط/غير نشط).
    """
    member_ref = db.collection('users').document(user_id).collection('members').document(member_id)
    member_ref.update({'is_active': is_active})
    return True

def add_book_and_challenge(user_id: str, book_info: dict, challenge_info: dict, rules_info: dict):
    """
    يضيف كتابًا جديدًا وتحديًا جديدًا بقواعده الخاصة لمستخدم معين.
    """
    try:
        books_ref = db.collection('users').document(user_id).collection('books')
        existing_books_query = books_ref.where('title', '==', book_info['title']).limit(1)
        if len(list(existing_books_query.stream())) > 0:
            return False, f"خطأ: كتاب بعنوان '{book_info['title']}' موجود بالفعل في قاعدة البيانات."

        book_ref = books_ref.add({
            'title': book_info['title'],
            'author': book_info['author'],
            'publication_year': book_info['year']
        })
        book_id = book_ref[1].id

        challenge_data = {**challenge_info, **rules_info, 'common_book_id': book_id}
        db.collection('users').document(user_id).collection('periods').add(challenge_data)
        
        return True, "تمت إضافة التحدي بنجاح."
    except Exception as e:
        return False, f"خطأ في قاعدة البيانات: {e}"

def add_log_and_achievements(user_id: str, log_data: dict, achievements_to_add: list):
    """
    يضيف سجل قراءة ومجموعة من الإنجازات دفعة واحدة.
    """
    logs_ref = db.collection('users').document(user_id).collection('logs')
    achievements_ref = db.collection('users').document(user_id).collection('achievements')
    
    batch = db.batch()
    
    new_log_ref = logs_ref.document()
    batch.set(new_log_ref, log_data)
    
    for ach_data in achievements_to_add:
        new_ach_ref = achievements_ref.document()
        batch.set(new_ach_ref, ach_data)
        
    batch.commit()

def clear_subcollection(user_id: str, collection_name: str):
    """
    يمسح جميع المستندات من مجموعة فرعية معينة لمستخدم.
    """
    coll_ref = db.collection('users').document(user_id).collection(collection_name)
    docs = list(coll_ref.stream())
    for doc in docs:
        doc.reference.delete()
    return True

def rebuild_stats_tables(user_id: str, member_stats_data: list):
    """
    يعيد بناء جدول إحصائيات الأعضاء.
    """
    clear_subcollection(user_id, 'member_stats')
    
    stats_ref = db.collection('users').document(user_id).collection('member_stats')
    for stats in member_stats_data:
        member_id = stats.pop('member_id') 
        stats_ref.document(member_id).set(stats)

def delete_challenge(user_id: str, period_id: str):
    """
    يحذف تحديًا معينًا وجميع البيانات المرتبطة به.
    """
    period_ref = db.collection('users').document(user_id).collection('periods').document(period_id)
    period_doc = period_ref.get()
    
    if not period_doc.exists:
        return False

    book_id = period_doc.to_dict().get('common_book_id')

    ach_ref = db.collection('users').document(user_id).collection('achievements')
    ach_to_delete = ach_ref.where('period_id', '==', period_id).stream()
    for doc in ach_to_delete:
        doc.reference.delete()
    
    period_ref.delete()
    
    if book_id:
        other_periods_query = db.collection('users').document(user_id).collection('periods').where('common_book_id', '==', book_id).limit(1)
        if len(list(other_periods_query.stream())) == 0:
            db.collection('users').document(user_id).collection('books').document(book_id).delete()
            
    return True

def save_refresh_token(user_id: str, refresh_token: str):
    """
    Saves the user's refresh_token to their settings document in Firestore.
    """
    try:
        settings_ref = db.collection('users').document(user_id).collection('settings').document('config')
        settings_ref.update({'refresh_token': refresh_token})
        return True
    except Exception as e:
        print(f"Error saving refresh token for user {user_id}: {e}")
        return False

def get_refresh_token(user_id: str):
    """
    Retrieves the user's refresh_token from their settings document in Firestore.
    """
    try:
        settings_ref = db.collection('users').document(user_id).collection('settings').document('config')
        doc = settings_ref.get()
        if doc.exists:
            return doc.to_dict().get('refresh_token')
        return None
    except Exception as e:
        print(f"Error getting refresh token for user {user_id}: {e}")
        return None

# --- NEW ROBUST DELETE FUNCTION ---
def delete_user_workspace(user_id: str):
    """
    Deletes a user's entire workspace from Firestore, including all subcollections.
    This is a destructive and irreversible action.
    """
    user_doc_ref = db.collection('users').document(user_id)

    # Recursively delete all documents in all subcollections
    subcollections = user_doc_ref.collections()
    for subcollection in subcollections:
        # Delete documents in batches for efficiency
        docs = subcollection.limit(100).stream()
        deleted = 0
        while True:
            batch = db.batch()
            doc_count = 0
            for doc in docs:
                batch.delete(doc.reference)
                doc_count += 1
            if doc_count == 0:
                break
            batch.commit()
            deleted += doc_count
            docs = subcollection.limit(100).stream()

    # Finally, delete the main user document itself
    user_doc_ref.delete()
    return True
