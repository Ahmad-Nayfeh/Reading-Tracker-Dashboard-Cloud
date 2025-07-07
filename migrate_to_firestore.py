import sqlite3
import pandas as pd
import firebase_client  # نستورد ملف الاتصال الذي أنشأناه
import os

# --- Constants ---
DB_FOLDER = 'data'
DB_NAME = 'reading_tracker.db'
DB_PATH = os.path.join(DB_FOLDER, DB_NAME)

def get_sqlite_connection():
    """Establishes a connection to the local SQLite database."""
    if not os.path.exists(DB_PATH):
        print(f"❌ خطأ: لم يتم العثور على قاعدة البيانات المحلية في المسار: {DB_PATH}")
        print("يرجى التأكد من أن ملف 'reading_tracker.db' موجود داخل مجلد 'data'.")
        return None
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def migrate_table_to_firestore(table_name, firestore_db, sqlite_conn, id_map=None, fk_maps=None):
    """
    Generic function to migrate a table from SQLite to a Firestore collection.
    
    :param table_name: Name of the SQLite table.
    :param firestore_db: Firestore client instance.
    :param sqlite_conn: SQLite connection instance.
    :param id_map: A dictionary to store the mapping from old ID to new ID.
    :param fk_maps: A dictionary of foreign key maps to update relationships.
    """
    print(f"🚚  جاري نقل جدول: {table_name}...")
    
    try:
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", sqlite_conn)
    except pd.io.sql.DatabaseError:
        print(f"🟡  تنبيه: الجدول '{table_name}' غير موجود في قاعدة البيانات المحلية. سيتم تخطي النقل.")
        return

    if df.empty:
        print(f"💨  الجدول '{table_name}' فارغ. لا توجد بيانات لنقلها.")
        return

    collection_ref = firestore_db.collection(table_name)
    batch = firestore_db.batch()
    
    # Get the primary key column name (e.g., 'member_id' for 'Members')
    pk_column = df.columns[0]

    for index, row in df.iterrows():
        row_dict = dict(row)
        old_id = row_dict.pop(pk_column) # Remove old PK from dict
        
        # Update foreign keys if any
        if fk_maps:
            for fk_column, fk_map in fk_maps.items():
                if fk_column in row_dict and row_dict[fk_column] in fk_map:
                    row_dict[fk_column] = fk_map[row_dict[fk_column]]

        # Create a new document in Firestore
        new_doc_ref = collection_ref.document()
        batch.set(new_doc_ref, row_dict)
        
        # Store the ID mapping if needed
        if id_map is not None:
            id_map[old_id] = new_doc_ref.id

    batch.commit()
    print(f"✅  تم نقل {len(df)} سجل من جدول '{table_name}' بنجاح!")


def main_migration():
    """Main function to orchestrate the entire migration process."""
    print("--- 🚀 بدء عملية نقل البيانات من SQLite إلى Firestore ---")
    
    sqlite_conn = get_sqlite_connection()
    if not sqlite_conn:
        return
        
    firestore_db = firebase_client.get_db_client()
    
    # --- ID Mappings ---
    # These are crucial to maintain relationships between tables
    member_id_map = {}
    book_id_map = {}
    period_id_map = {}

    # --- Migration Order is Important ---
    # 1. Tables without foreign keys
    migrate_table_to_firestore('Members', firestore_db, sqlite_conn, id_map=member_id_map)
    migrate_table_to_firestore('Books', firestore_db, sqlite_conn, id_map=book_id_map)
    
    # 2. Tables with foreign keys
    migrate_table_to_firestore('ChallengePeriods', firestore_db, sqlite_conn, id_map=period_id_map, fk_maps={'common_book_id': book_id_map})
    migrate_table_to_firestore('ReadingLogs', firestore_db, sqlite_conn, fk_maps={'member_id': member_id_map})
    migrate_table_to_firestore('Achievements', firestore_db, sqlite_conn, fk_maps={'member_id': member_id_map, 'period_id': period_id_map, 'book_id': book_id_map})
    
    # 3. Settings tables (special handling)
    print("🚚  جاري نقل جدول: AppSettings...")
    app_settings_df = pd.read_sql_query("SELECT * FROM AppSettings", sqlite_conn)
    app_settings_ref = firestore_db.collection('AppSettings')
    for index, row in app_settings_df.iterrows():
        app_settings_ref.document(row['key']).set({'value': row['value']})
    print(f"✅  تم نقل {len(app_settings_df)} إعداد بنجاح!")

    print("🚚  جاري نقل جدول: GlobalSettings...")
    global_settings_df = pd.read_sql_query("SELECT * FROM GlobalSettings WHERE setting_id = 1", sqlite_conn)
    if not global_settings_df.empty:
        settings_dict_raw = dict(global_settings_df.iloc[0])
        settings_dict_raw.pop('setting_id', None)
        
        # *** THE FIX IS HERE ***
        # Convert all numpy number types to native Python int
        settings_dict_clean = {key: int(value) for key, value in settings_dict_raw.items()}
        
        firestore_db.collection('GlobalSettings').document('default').set(settings_dict_clean)
        print("✅  تم نقل الإعدادات العامة بنجاح!")

    sqlite_conn.close()
    print("\n--- 🎉 اكتملت عملية نقل البيانات بنجاح! ---")
    print("يمكنك الآن تشغيل التطبيق الرئيسي. جميع بياناتك أصبحت في السحابة.")

if __name__ == '__main__':
    main_migration()
