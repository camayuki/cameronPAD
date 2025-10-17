"""
Migrate notes data from app.db to cameronpad_dev.db
"""
import sqlite3

def migrate_notes():
    # Connect to source database (original app)
    source_conn = sqlite3.connect('data/app.db')
    source_cur = source_conn.cursor()
    
    # Connect to target database (new app)
    target_conn = sqlite3.connect('data/cameronpad_dev.db')
    target_cur = target_conn.cursor()
    
    # Fetch all notes from source
    print("Fetching notes from app.db...")
    source_cur.execute("SELECT id, content, ts FROM notes ORDER BY ts")
    notes = source_cur.fetchall()
    
    print(f"Found {len(notes)} note(s) in source database")
    
    if not notes:
        print("No notes to migrate!")
        source_conn.close()
        target_conn.close()
        return
    
    # Display notes
    print("\n=== Notes to migrate ===")
    for note in notes:
        note_id, content, timestamp = note
        print(f"\nID: {note_id}")
        print(f"Timestamp: {timestamp}")
        print(f"Content: {content[:200]}..." if len(content) > 200 else f"Content: {content}")
        print("---")
    
    # Migrate to target database
    print("\nMigrating to cameronpad_dev.db...")
    migrated = 0
    
    for note in notes:
        note_id, content, timestamp = note
        try:
            # Insert note (let database auto-generate new ID)
            target_cur.execute(
                "INSERT INTO notes(content, ts) VALUES(?, ?)",
                (content, timestamp)
            )
            migrated += 1
        except Exception as e:
            print(f"Error migrating note ID {note_id}: {e}")
    
    target_conn.commit()
    
    print(f"\n✅ Successfully migrated {migrated}/{len(notes)} notes")
    
    # Verify migration
    target_cur.execute("SELECT COUNT(*) FROM notes")
    count = target_cur.fetchone()[0]
    print(f"Total notes in target database: {count}")
    
    source_conn.close()
    target_conn.close()

if __name__ == "__main__":
    migrate_notes()
