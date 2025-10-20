"""
Test script to verify group-based privacy is working correctly
"""
import sqlite3

def test_privacy():
    conn = sqlite3.connect('data/cameronpad_dev.db')
    cur = conn.cursor()
    
    print("=" * 60)
    print("GROUP-BASED PRIVACY TEST")
    print("=" * 60)
    
    # Show all users and their groups
    print("\n📊 USERS AND GROUPS:")
    print("-" * 60)
    cur.execute("""
        SELECT u.id, u.username, GROUP_CONCAT(g.name, ', ') as groups
        FROM users u
        LEFT JOIN user_groups ug ON u.id = ug.user_id
        LEFT JOIN groups g ON ug.group_id = g.id
        GROUP BY u.id
        ORDER BY u.id
    """)
    users = cur.fetchall()
    for user_id, username, groups in users:
        print(f"User {user_id:2d} ({username:15s}): {groups or 'NO GROUPS'}")
    
    # Show all notes and which groups they belong to
    print("\n📝 NOTES AND THEIR GROUPS:")
    print("-" * 60)
    cur.execute("""
        SELECT n.id, n.user_id, u.username, n.group_id, g.name as group_name,
               substr(n.content, 1, 30) as preview
        FROM notes n
        LEFT JOIN users u ON n.user_id = u.id
        LEFT JOIN groups g ON n.group_id = g.id
        ORDER BY n.id
    """)
    notes = cur.fetchall()
    if notes:
        for note_id, user_id, username, group_id, group_name, preview in notes:
            print(f"Note {note_id:2d}: created_by={username or 'unknown':10s}, "
                  f"group={group_name or 'NONE':10s} (id:{group_id}), "
                  f"content='{preview}...'")
    else:
        print("No notes in database")
    
    # Show all notepad tabs and their groups
    print("\n📓 NOTEPAD TABS AND THEIR GROUPS:")
    print("-" * 60)
    cur.execute("""
        SELECT p.id, p.name, p.user_id, u.username, p.group_id, g.name as group_name
        FROM pad_tabs p
        LEFT JOIN users u ON p.user_id = u.id
        LEFT JOIN groups g ON p.group_id = g.id
        ORDER BY p.id
    """)
    tabs = cur.fetchall()
    if tabs:
        for tab_id, tab_name, user_id, username, group_id, group_name in tabs:
            print(f"Tab {tab_id:2d} ({tab_name:15s}): created_by={username or 'unknown':10s}, "
                  f"group={group_name or 'NONE':10s} (id:{group_id})")
    else:
        print("No tabs in database")
    
    # Simulate what each user would see (notes)
    print("\n🔒 PRIVACY TEST - WHO SEES WHAT (NOTES):")
    print("-" * 60)
    for user_id, username, _ in users:
        cur.execute("""
            SELECT DISTINCT n.id
            FROM notes n
            INNER JOIN user_groups ug ON n.group_id = ug.group_id
            WHERE ug.user_id = ?
            ORDER BY n.id
        """, (user_id,))
        visible_notes = [str(r[0]) for r in cur.fetchall()]
        print(f"User {user_id:2d} ({username:15s}) can see notes: {', '.join(visible_notes) if visible_notes else 'NONE'}")
    
    # Simulate what each user would see (notepad tabs)
    print("\n🔒 PRIVACY TEST - WHO SEES WHAT (NOTEPAD TABS):")
    print("-" * 60)
    for user_id, username, _ in users:
        cur.execute("""
            SELECT DISTINCT p.id, p.name
            FROM pad_tabs p
            INNER JOIN user_groups ug ON p.group_id = ug.group_id
            WHERE ug.user_id = ?
            ORDER BY p.id
        """, (user_id,))
        visible_tabs = cur.fetchall()
        tab_list = [f"{t[0]}({t[1]})" for t in visible_tabs]
        print(f"User {user_id:2d} ({username:15s}) can see tabs: {', '.join(tab_list) if tab_list else 'NONE'}")
    
    # Check for orphaned content (content not in any group)
    print("\n⚠️  ORPHANED CONTENT CHECK:")
    print("-" * 60)
    cur.execute("SELECT COUNT(*) FROM notes WHERE group_id IS NULL")
    orphan_notes = cur.fetchone()[0]
    print(f"Notes with no group: {orphan_notes}")
    
    cur.execute("SELECT COUNT(*) FROM pad_tabs WHERE group_id IS NULL")
    orphan_tabs = cur.fetchone()[0]
    print(f"Tabs with no group: {orphan_tabs}")
    
    if orphan_notes > 0 or orphan_tabs > 0:
        print("\n⚠️  WARNING: Orphaned content found! Run migrate_groups.py to fix.")
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ Privacy Test Complete!")
    print("=" * 60)
    print(f"Total users: {len(users)}")
    print(f"Total notes: {len(notes)}")
    print(f"Total tabs: {len(tabs)}")
    print(f"Orphaned content: {orphan_notes + orphan_tabs}")
    print("\nPrivacy is ACTIVE if:")
    print("  ✓ Users in different groups see different content")
    print("  ✓ Users with NO groups see NOTHING")
    print("  ✓ All content has a group_id assigned")
    print("=" * 60)
    
    conn.close()

if __name__ == "__main__":
    test_privacy()
