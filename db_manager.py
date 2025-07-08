import pandas as pd
from firebase_config import db # استيراد عميل قاعدة البيانات المهيأ

# --- بنية قاعدة البيانات في Firestore ---
# users (collection)
#  └── {user_id} (document) - يمثل مساحة عمل كل مشرف
#      ├── settings (document) - يحتوي على إعدادات المشرف مثل رابط الشيت
#      ├── global_rules (document) - يحتوي على نظام النقاط الافتراضي للمشرف
#      │
#      ├── members (subcollection)
#      │    └── {member_id} (document)
#      │
#      ├── books (subcollection)
#      │    └── {book_id} (document)
#      │
#      ├── periods (subcollection)
#      │    └── {period_id} (document)
#      │
#      ├── logs (subcollection)
#      │    └── {log_id} (document)
#      │
#      ├── achievements (subcollection)
#      │    └── {achievement_id} (document)
#      │
#      └── member_stats (subcollection)
#           └── {member_id} (document)
# -------------------------------------------------


def check_user_exists(user_id: str):
    """
    يتحقق مما إذا كان للمستخدم مساحة عمل موجودة في Firestore.
    
    Args:
        user_id (str): المعرف الفريد للمستخدم من جوجل.

    Returns:
        bool: True إذا كان المستخدم موجودًا، وإلا False.
    """
    user_doc_ref = db.collection('users').document(user_id)
    return user_doc_ref.get().exists

def create_new_user_workspace(user_id: str, user_email: str):
    """
    ينشئ مساحة عمل جديدة لمشرف جديد عند تسجيل الدخول لأول مرة.
    
    Args:
        user_id (str): المعرف الفريد للمستخدم.
        user_email (str): البريد الإلكتروني للمستخدم.
    """
    user_doc_ref = db.collection('users').document(user_id)
    
    # إنشاء المستند الرئيسي للمستخدم مع بعض المعلومات الأساسية
    user_doc_ref.set({
        'email': user_email,
        'created_at': pd.Timestamp.now()
    })
    
    # إنشاء مستند الإعدادات الافتراضية
    user_doc_ref.collection('settings').document('config').set({
        'spreadsheet_url': '',
        'form_url': '',
        'form_id': '',
        'member_question_id': ''
    })
    
    # إنشاء مستند نظام النقاط الافتراضي
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
        doc_data[f'{collection_name}_id'] = doc.id # إضافة معرّف المستند
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

    # دمج بيانات الكتب مع التحديات
    if not periods_df.empty and not books_df.empty:
        # إعادة تسمية الأعمدة لتجنب التضارب
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
    return len(query.get()) > 0

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
        # التحقق مما إذا كان الكتاب موجودًا بالفعل لهذا المستخدم
        books_ref = db.collection('users').document(user_id).collection('books')
        existing_books = books_ref.where('title', '==', book_info['title']).limit(1).get()
        if len(existing_books) > 0:
            return False, f"خطأ: كتاب بعنوان '{book_info['title']}' موجود بالفعل في قاعدة البيانات."

        # إضافة الكتاب
        book_ref = books_ref.add({
            'title': book_info['title'],
            'author': book_info['author'],
            'publication_year': book_info['year']
        })
        book_id = book_ref[1].id # الحصول على معرف المستند الجديد

        # إضافة التحدي مع ربطه بمعرف الكتاب
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
    
    # استخدام batch لضمان تنفيذ جميع العمليات معًا أو فشلها معًا
    batch = db.batch()
    
    # إضافة سجل القراءة
    new_log_ref = logs_ref.document()
    batch.set(new_log_ref, log_data)
    
    # إضافة الإنجازات
    for ach_data in achievements_to_add:
        new_ach_ref = achievements_ref.document()
        batch.set(new_ach_ref, ach_data)
        
    batch.commit()

def clear_subcollection(user_id: str, collection_name: str):
    """
    يمسح جميع المستندات من مجموعة فرعية معينة لمستخدم.
    """
    coll_ref = db.collection('users').document(user_id).collection(collection_name)
    docs = coll_ref.stream()
    for doc in docs:
        doc.reference.delete()
    return True

def rebuild_stats_tables(user_id: str, member_stats_data: list):
    """
    يعيد بناء جدول إحصائيات الأعضاء.
    """
    # أولاً، مسح الإحصائيات القديمة
    clear_subcollection(user_id, 'member_stats')
    
    # ثانياً، إضافة الإحصائيات الجديدة
    stats_ref = db.collection('users').document(user_id).collection('member_stats')
    for stats in member_stats_data:
        # استخدام member_id كمعرف للمستند لسهولة الوصول
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

    # حذف الإنجازات المرتبطة بهذا التحدي
    ach_ref = db.collection('users').document(user_id).collection('achievements')
    ach_to_delete = ach_ref.where('period_id', '==', period_id).stream()
    for doc in ach_to_delete:
        doc.reference.delete()
    
    # حذف التحدي نفسه
    period_ref.delete()
    
    # التحقق مما إذا كان الكتاب مرتبطًا بتحديات أخرى قبل حذفه
    if book_id:
        other_periods = db.collection('users').document(user_id).collection('periods')\
                          .where('common_book_id', '==', book_id).limit(1).get()
        if len(other_periods) == 0:
            # إذا لم يكن مرتبطًا، احذف الكتاب
            db.collection('users').document(user_id).collection('books').document(book_id).delete()
            
    return True
