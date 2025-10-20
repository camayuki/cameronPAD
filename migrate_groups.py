"""
One-time migration to assign notes/journals/notepads to user's groups.
This script updates existing entries to be in the same groups as their creators.
"""
import sqlite3

def migrate_group_assignments():
    conn = sqlite3.connect('data/cameronpad_dev.db')
    cur = conn.cursor()
    
    # First, check what tables exist
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    all_tables = [row[0] for row in cur.fetchall()]
    print(f"All tables: {all_tables}")
    
    note_tables = [t for t in all_tables if 'note' in t.lower() or 'journal' in t.lower()]
    print(f"\nTables to migrate: {note_tables}")
    
    # Check user groups
    print("\n=== USER GROUPS ===")
    cur.execute("""
        SELECT u.id, u.username, GROUP_CONCAT(g.name) as groups
        FROM users u
        LEFT JOIN user_groups ug ON u.id = ug.user_id
        LEFT JOIN groups g ON ug.group_id = g.id
        GROUP BY u.id
    """)
    user_groups = cur.fetchall()
    for user in user_groups:
        print(f"User {user[0]} ({user[1]}): {user[2]}")
    
    # Migrate notes
    print("\n=== MIGRATING NOTES ===")
    if 'notes' in all_tables:
        cur.execute("PRAGMA table_info(notes)")
        note_cols = [col[1] for col in cur.fetchall()]
        print(f"Notes columns: {note_cols}")
        
        if 'user_id' in note_cols and 'group_id' in note_cols:
            # Get all notes with user_id but missing or wrong group_id
            cur.execute("SELECT id, user_id, group_id FROM notes WHERE user_id IS NOT NULL")
            notes = cur.fetchall()
            print(f"Found {len(notes)} notes to check")
            
            for note_id, user_id, current_group_id in notes:
                # Get the first group this user belongs to (prefer Admins if available)
                cur.execute("""
                    SELECT g.id, g.name 
                    FROM user_groups ug 
                    JOIN groups g ON ug.group_id = g.id 
                    WHERE ug.user_id = ?
                    ORDER BY CASE WHEN g.name = 'Admins' THEN 0 ELSE 1 END
                    LIMIT 1
                """, (user_id,))
                
                user_group = cur.fetchone()
                if user_group:
                    new_group_id, group_name = user_group
                    if current_group_id != new_group_id:
                        cur.execute("UPDATE notes SET group_id = ? WHERE id = ?", (new_group_id, note_id))
                        print(f"  Note {note_id}: user {user_id} → group {new_group_id} ({group_name})")
                    else:
                        print(f"  Note {note_id}: already in correct group ({group_name})")
    
    # Migrate notepad entries
    print("\n=== MIGRATING NOTEPAD ENTRIES ===")
    if 'pad_tabs' in all_tables:
        cur.execute("PRAGMA table_info(pad_tabs)")
        notepad_cols = [col[1] for col in cur.fetchall()]
        print(f"Notepad columns: {notepad_cols}")
        
        if 'group_id' in notepad_cols:
            # Get all tabs that don't have a group assigned
            cur.execute("SELECT id, user_id, group_id FROM pad_tabs WHERE group_id IS NULL OR user_id IS NULL")
            orphaned_tabs = cur.fetchall()
            print(f"Found {len(orphaned_tabs)} orphaned notepad tabs")
            
            # Assign orphaned tabs to the Admins group (since we don't know who created them)
            cur.execute("SELECT id FROM groups WHERE name = 'Admins'")
            admins_group = cur.fetchone()
            if admins_group and orphaned_tabs:
                admins_group_id = admins_group[0]
                for tab_id, user_id, current_group_id in orphaned_tabs:
                    cur.execute("UPDATE pad_tabs SET group_id = ? WHERE id = ?", (admins_group_id, tab_id))
                    print(f"  Tab {tab_id}: assigned to Admins group (orphaned content)")
            
            # Now migrate tabs that have user_id but need group verification
            cur.execute("SELECT id, user_id, group_id FROM pad_tabs WHERE user_id IS NOT NULL AND group_id IS NOT NULL")
            notepads = cur.fetchall()
            print(f"Found {len(notepads)} notepad entries with users to verify")
            
            for entry_id, user_id, current_group_id in notepads:
                cur.execute("""
                    SELECT g.id, g.name 
                    FROM user_groups ug 
                    JOIN groups g ON ug.group_id = g.id 
                    WHERE ug.user_id = ?
                    ORDER BY CASE WHEN g.name = 'Admins' THEN 0 ELSE 1 END
                    LIMIT 1
                """, (user_id,))
                
                user_group = cur.fetchone()
                if user_group:
                    new_group_id, group_name = user_group
                    if current_group_id != new_group_id:
                        cur.execute("UPDATE pad_tabs SET group_id = ? WHERE id = ?", (new_group_id, entry_id))
                        print(f"  Tab {entry_id}: user {user_id} → group {new_group_id} ({group_name})")
                    else:
                        print(f"  Tab {entry_id}: already in correct group ({group_name})")
        else:
            print("⚠️  pad_tabs table doesn't have group_id column yet")
    
    # Migrate journal entries
    print("\n=== MIGRATING JOURNAL ENTRIES ===")
    if 'journal_entries' in all_tables:
        cur.execute("PRAGMA table_info(journal_entries)")
        journal_cols = [col[1] for col in cur.fetchall()]
        print(f"Journal columns: {journal_cols}")
        
        if 'user_id' in journal_cols and 'group_id' in journal_cols:
            cur.execute("SELECT id, user_id, group_id FROM journal_entries WHERE user_id IS NOT NULL")
            journals = cur.fetchall()
            print(f"Found {len(journals)} journal entries to check")
            
            for entry_id, user_id, current_group_id in journals:
                cur.execute("""
                    SELECT g.id, g.name 
                    FROM user_groups ug 
                    JOIN groups g ON ug.group_id = g.id 
                    WHERE ug.user_id = ?
                    ORDER BY CASE WHEN g.name = 'Admins' THEN 0 ELSE 1 END
                    LIMIT 1
                """, (user_id,))
                
                user_group = cur.fetchone()
                if user_group:
                    new_group_id, group_name = user_group
                    if current_group_id != new_group_id:
                        cur.execute("UPDATE journal_entries SET group_id = ? WHERE id = ?", (new_group_id, entry_id))
                        print(f"  Journal {entry_id}: user {user_id} → group {new_group_id} ({group_name})")
                    else:
                        print(f"  Journal {entry_id}: already in correct group ({group_name})")
    
    # Commit changes
    conn.commit()
    print("\n✅ Migration completed successfully!")
    
    # Verify
    print("\n=== VERIFICATION ===")
    if 'notes' in all_tables:
        cur.execute("""
            SELECT n.id, n.user_id, n.group_id, g.name as group_name, u.username
            FROM notes n
            LEFT JOIN groups g ON n.group_id = g.id
            LEFT JOIN users u ON n.user_id = u.id
        """)
        print("Notes:")
        for row in cur.fetchall():
            print(f"  Note {row[0]}: user={row[4] or 'unknown'} (id:{row[1]}), group={row[3]} (id:{row[2]})")
    
    if 'pad_tabs' in all_tables:
        cur.execute("""
            SELECT p.id, p.name, p.user_id, p.group_id, g.name as group_name, u.username
            FROM pad_tabs p
            LEFT JOIN groups g ON p.group_id = g.id
            LEFT JOIN users u ON p.user_id = u.id
            LIMIT 5
        """)
        print("\nNotepad Tabs (first 5):")
        for row in cur.fetchall():
            print(f"  Tab {row[0]} ({row[1]}): user={row[5] or 'unknown'} (id:{row[2]}), group={row[4]} (id:{row[3]})")
    
    conn.close()

if __name__ == "__main__":
    migrate_group_assignments()
