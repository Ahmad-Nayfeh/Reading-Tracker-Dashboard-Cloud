import pandas as pd
from firebase_admin import firestore
import firebase_client

# --- Helper to get the user's workspace reference ---
def _get_db_and_workspace(user_id):
    """Returns the main db client and a reference to the user's workspace."""
    db = firebase_client.get_db_client()
    workspace_ref = db.collection('Workspaces').document(user_id)
    return db, workspace_ref

# --- Helper function to convert Firestore collection to list of dicts ---
def _collection_to_list(collection_ref):
    """Converts a Firestore collection snapshot to a list of dictionaries."""
    docs = []
    for doc in collection_ref.stream():
        doc_dict = doc.to_dict()
        doc_dict['id'] = doc.id
        docs.append(doc_dict)
    return docs

# --- AppSettings Functions (Now User-Specific) ---
def set_setting(user_id, key, value):
    """Saves or updates a key-value pair in a user's AppSettings sub-collection."""
    db, workspace_ref = _get_db_and_workspace(user_id)
    try:
        settings_ref = workspace_ref.collection('AppSettings').document(key)
        settings_ref.set({'value': str(value)})
    except Exception as e:
        print(f"Firestore error in set_setting: {e}")

def get_setting(user_id, key):
    """Retrieves a value by its key from a user's AppSettings sub-collection."""
    db, workspace_ref = _get_db_and_workspace(user_id)
    try:
        doc_ref = workspace_ref.collection('AppSettings').document(key)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict().get('value')
        return None
    except Exception as e:
        print(f"Firestore error in get_setting: {e}")
        return None

# --- READ Functions (Now User-Specific) ---
def get_all_data_for_stats(user_id):
    """Fetches all data needed for the calculation engine from a user's workspace."""
    db, workspace_ref = _get_db_and_workspace(user_id)
    try:
        members_ref = workspace_ref.collection('Members').order_by('name')
        logs_ref = workspace_ref.collection('ReadingLogs')
        achievements_ref = workspace_ref.collection('Achievements')
        periods_ref = workspace_ref.collection('ChallengePeriods').order_by('start_date', direction=firestore.Query.DESCENDING)
        books_ref = workspace_ref.collection('Books')

        members = _collection_to_list(members_ref)
        logs = _collection_to_list(logs_ref)
        achievements = _collection_to_list(achievements_ref)
        periods_raw = _collection_to_list(periods_ref)
        books_list = _collection_to_list(books_ref)

        books_map = {book['id']: book for book in books_list}
        periods = []
        for period in periods_raw:
            book_id = period.get('common_book_id')
            if book_id in books_map:
                book_data = books_map[book_id]
                period['title'] = book_data.get('title')
                period['author'] = book_data.get('author')
                period['publication_year'] = book_data.get('publication_year')
                periods.append(period)

        for m in members: m['member_id'] = m.pop('id')
        for p in periods: p['period_id'] = p.pop('id')

    except Exception as e:
        print(f"Error fetching all data from Firestore for user {user_id}: {e}")
        return None

    return {"members": members, "logs": logs, "achievements": achievements, "periods": periods}

def get_table_as_df(user_id, table_name):
    """Fetches an entire sub-collection and returns it as a Pandas DataFrame."""
    db, workspace_ref = _get_db_and_workspace(user_id)
    try:
        collection_ref = workspace_ref.collection(table_name)
        docs = _collection_to_list(collection_ref)
        df = pd.DataFrame(docs)
        if 'id' in df.columns:
             pk_name = f"{table_name.lower().rstrip('s')}_id"
             df.rename(columns={'id': pk_name}, inplace=True)
    except Exception as e:
        print(f"Error reading collection {table_name} for user {user_id}: {e}")
        df = pd.DataFrame()
    return df

def has_achievement(user_id, member_id, achievement_type, period_id):
    """Checks if a specific achievement already exists for a member in a period."""
    db, workspace_ref = _get_db_and_workspace(user_id)
    try:
        achievements_ref = workspace_ref.collection('Achievements')
        query = achievements_ref.where('member_id', '==', member_id)\
                                .where('achievement_type', '==', achievement_type)\
                                .where('period_id', '==', period_id)\
                                .limit(1)
        return len(list(query.stream())) > 0
    except Exception as e:
        print(f"Firestore error in has_achievement: {e}")
        return False

# --- WRITE/UPDATE Functions (Now User-Specific) ---
def add_members(user_id, names_list):
    """Adds a list of new members to a user's Members sub-collection."""
    db, workspace_ref = _get_db_and_workspace(user_id)
    # *** THE FIX IS HERE ***
    batch = db.batch()
    members_ref = workspace_ref.collection('Members')
    for name in names_list:
        existing_member_query = members_ref.where('name', '==', name).limit(1)
        if not any(existing_member_query.stream()):
            new_member_ref = members_ref.document()
            batch.set(new_member_ref, {'name': name, 'is_active': True})
    batch.commit()

def add_single_member(user_id, name):
    """Adds or reactivates a single member in a user's workspace."""
    db, workspace_ref = _get_db_and_workspace(user_id)
    members_ref = workspace_ref.collection('Members')
    try:
        query = members_ref.where('name', '==', name).limit(1)
        existing_members = list(query.stream())
        if existing_members:
            member_doc = existing_members[0]
            if member_doc.to_dict().get('is_active'):
                return ('exists', f"العضو '{name}' موجود ونشط بالفعل.")
            else:
                member_doc.reference.update({'is_active': True})
                return ('reactivated', f"تمت إعادة تنشيط العضو '{name}' بنجاح.")
        else:
            members_ref.add({'name': name, 'is_active': True})
            return ('added', f"تمت إضافة العضو الجديد '{name}' بنجاح.")
    except Exception as e:
        return ('error', f"Firestore error: {e}")

def set_member_status(user_id, member_id, is_active: bool):
    """Sets a member's status in a user's workspace."""
    db, workspace_ref = _get_db_and_workspace(user_id)
    try:
        member_ref = workspace_ref.collection('Members').document(member_id)
        member_ref.update({'is_active': is_active})
        return True
    except Exception as e:
        print(f"Firestore error in set_member_status: {e}")
        return False

def add_book_and_challenge(user_id, book_info, challenge_info, rules_info):
    """Adds a new book and challenge to a user's workspace."""
    db, workspace_ref = _get_db_and_workspace(user_id)
    try:
        books_ref = workspace_ref.collection('Books')
        existing_book_query = books_ref.where('title', '==', book_info['title']).limit(1)
        if any(existing_book_query.stream()):
            return False, f"خطأ: كتاب بعنوان '{book_info['title']}' موجود بالفعل في قاعدة البيانات."

        book_data = {'title': book_info['title'], 'author': book_info['author'], 'publication_year': book_info['year']}
        update_time, book_ref = workspace_ref.collection('Books').add(book_data)
        book_id = book_ref.id

        challenge_data = {'start_date': challenge_info['start_date'], 'end_date': challenge_info['end_date'], 'common_book_id': book_id, **rules_info}
        workspace_ref.collection('ChallengePeriods').add(challenge_data)
        return True, "تمت إضافة التحدي بنجاح."
    except Exception as e:
        return False, f"خطأ في قاعدة البيانات: {e}"

def add_log_and_achievements(user_id, log_data, achievements_to_add):
    """Adds a log and achievements to a user's workspace."""
    db, workspace_ref = _get_db_and_workspace(user_id)
    # *** THE FIX IS HERE ***
    batch = db.batch()
    log_ref = workspace_ref.collection('ReadingLogs').document()
    batch.set(log_ref, log_data)
    if achievements_to_add:
        achievements_ref = workspace_ref.collection('Achievements')
        for ach_data_tuple in achievements_to_add:
            ach_ref = achievements_ref.document()
            ach_data_dict = {"member_id": ach_data_tuple[0], "achievement_type": ach_data_tuple[1], "achievement_date": ach_data_tuple[2], "period_id": ach_data_tuple[3], "book_id": ach_data_tuple[4]}
            batch.set(ach_ref, ach_data_dict)
    batch.commit()

def _delete_collection(db, coll_ref, batch_size=50):
    """Deletes all documents in a collection in batches."""
    docs = coll_ref.limit(batch_size).stream()
    deleted = 0
    # *** THE FIX IS HERE ***
    batch = db.batch()
    for doc in docs:
        batch.delete(doc.reference)
        deleted += 1
    if deleted > 0:
        batch.commit()
        if deleted >= batch_size:
            return _delete_collection(db, coll_ref, batch_size)

def rebuild_stats_tables(user_id, member_stats_data, group_stats_data):
    """Rebuilds the stats sub-collections in a user's workspace."""
    db, workspace_ref = _get_db_and_workspace(user_id)
    _delete_collection(db, workspace_ref.collection('MemberStats'))
    _delete_collection(db, workspace_ref.collection('GroupStats'))
    # *** THE FIX IS HERE ***
    batch = db.batch()
    if member_stats_data:
        member_stats_ref = workspace_ref.collection('MemberStats')
        for stats in member_stats_data:
            doc_id = stats.pop('member_id')
            doc_ref = member_stats_ref.document(doc_id)
            batch.set(doc_ref, stats)
    if group_stats_data:
        group_stats_ref = workspace_ref.collection('GroupStats')
        for stats in group_stats_data:
            doc_id = stats.pop('period_id')
            doc_ref = group_stats_ref.document(doc_id)
            batch.set(doc_ref, stats)
    batch.commit()

def update_global_settings(user_id, settings_dict):
    """Updates the global settings document in a user's workspace."""
    db, workspace_ref = _get_db_and_workspace(user_id)
    try:
        settings_ref = workspace_ref.collection('GlobalSettings').document('default')
        settings_ref.set(settings_dict, merge=True)
        return True
    except Exception as e:
        return False

def load_global_settings(user_id):
    """Loads the global settings document from a user's workspace."""
    db, workspace_ref = _get_db_and_workspace(user_id)
    try:
        doc_ref = workspace_ref.collection('GlobalSettings').document('default')
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        else:
            default_settings = {"minutes_per_point_common": 10, "minutes_per_point_other": 5, "finish_common_book_points": 50, "finish_other_book_points": 25, "quote_common_book_points": 3, "quote_other_book_points": 1, "attend_discussion_points": 25}
            update_global_settings(user_id, default_settings)
            return default_settings
    except Exception as e:
        return None

def delete_challenge(user_id, period_id):
    """Deletes a challenge and its data from a user's workspace."""
    db, workspace_ref = _get_db_and_workspace(user_id)
    try:
        period_ref = workspace_ref.collection('ChallengePeriods').document(period_id)
        period_doc = period_ref.get()
        if not period_doc.exists: return True
        book_id = period_doc.to_dict().get('common_book_id')
        ach_query = workspace_ref.collection('Achievements').where('period_id', '==', period_id)
        _delete_collection(db, ach_query)
        workspace_ref.collection('GroupStats').document(period_id).delete()
        period_ref.delete()
        if book_id:
            other_challenges_query = workspace_ref.collection('ChallengePeriods').where('common_book_id', '==', book_id).limit(1)
            if not any(other_challenges_query.stream()):
                workspace_ref.collection('Books').document(book_id).delete()
        return True
    except Exception as e:
        return False

def clear_all_logs_and_achievements(user_id):
    """Wipes the logs and achievements sub-collections for a user."""
    db, workspace_ref = _get_db_and_workspace(user_id)
    try:
        _delete_collection(db, workspace_ref.collection('ReadingLogs'))
        _delete_collection(db, workspace_ref.collection('Achievements'))
        return True
    except Exception as e:
        return False
