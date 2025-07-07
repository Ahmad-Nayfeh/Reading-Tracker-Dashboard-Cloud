import firebase_client

def _delete_collection(db, coll_ref, batch_size=50):
    """
    Deletes all documents in a collection or query in batches.
    This is an efficient way to clear large collections.
    
    :param db: The main Firestore client object.
    :param coll_ref: The collection reference to delete documents from.
    """
    docs = coll_ref.limit(batch_size).stream()
    deleted = 0

    # *** THE FINAL FIX IS HERE ***
    # The batch object must be created from the main db client.
    batch = db.batch()
    
    for doc in docs:
        batch.delete(doc.reference)
        deleted += 1

    if deleted == 0:
        return

    batch.commit()
    print(f"  - تم حذف {deleted} مستند...")
    
    # Recurse on the same collection to delete the next batch.
    return _delete_collection(db, coll_ref, batch_size)


def main_cleanup():
    """Main function to orchestrate the cleanup of all collections."""
    print("--- ☢️ بدء عملية تنظيف قاعدة بيانات Firestore ---")
    print("تحذير: هذه العملية ستقوم بحذف جميع البيانات في المجموعات المحددة.")
    
    try:
        input("--> اضغط على مفتاح Enter للمتابعة، أو أغلق النافذة (Ctrl+C) للإلغاء...")
    except KeyboardInterrupt:
        print("\n🚫 تم إلغاء العملية.")
        return

    db = firebase_client.get_db_client()
    
    collections_to_delete = [
        'Members', 'Books', 'ChallengePeriods', 'ReadingLogs',
        'Achievements', 'AppSettings', 'GroupStats', 'MemberStats', 'GlobalSettings'
    ]

    for collection_name in collections_to_delete:
        print(f"\n🔥 جاري حذف مجموعة: {collection_name}...")
        try:
            coll_ref = db.collection(collection_name)
            # Pass the db client to the delete function
            _delete_collection(db, coll_ref)
            print(f"✅ اكتمل حذف مجموعة '{collection_name}'.")
        except Exception as e:
            print(f"🟡 حدث خطأ أثناء حذف مجموعة '{collection_name}': {e}.")

    print("\n--- 🎉 اكتملت عملية التنظيف بنجاح! ---")
    print("قاعدة بيانات Firestore أصبحت الآن فارغة وجاهزة لاستقبال البيانات النظيفة.")


if __name__ == '__main__':
    main_cleanup()