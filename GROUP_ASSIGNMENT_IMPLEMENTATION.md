# Group Assignment Implementation

## Overview
Implemented automatic group assignment for notes, journals, and notepads based on the user's group membership.

## Changes Made

### 1. Migration Script (`migrate_groups.py`)
- **Purpose**: One-time migration to assign existing content to user groups
- **What it does**:
  - Checks all notes, notepad entries, and journal entries
  - Assigns each entry to the creator's primary group
  - Prefers "Admins" group if user is in multiple groups
  - Falls back to first available group otherwise

**Run with**: `py migrate_groups.py`

### 2. Notes Plugin (`plugins/notes/plugin.py`)
- **Updated**: `add_note()` function
- **Changes**:
  - Now accepts `Request` parameter to get current user
  - Extracts user_id from request.state.user
  - Queries user's groups from database
  - Automatically assigns new note to user's primary group (prefers Admins)
  - Stores both user_id and group_id when creating notes

**Database columns used**:
- `notes.user_id`: ID of user who created the note
- `notes.group_id`: ID of group the note belongs to

### 3. Notepad Plugin (`plugins/notepad/plugin.py` and `database.py`)
- **Updated database.py**:
  - Added `user_id` and `group_id` columns to `pad_tabs` table
  - Added ALTER TABLE statements to add columns to existing databases
  - Added foreign key constraints

- **Updated plugin.py**:
  - Modified `add_tab()` function to accept Request parameter
  - Extracts current user information
  - Queries user's primary group
  - Assigns new tabs to user's group

**Database columns added**:
- `pad_tabs.user_id`: ID of user who created the tab
- `pad_tabs.group_id`: ID of group the tab belongs to

### 4. Journal Plugin
- **Status**: Not yet implemented (TODOs in place)
- **Reason**: Journal plugin doesn't have database persistence yet (still has TODO markers)
- **Future work**: When journal persistence is implemented, use same pattern as notes

## How It Works

### When Creating New Content:

1. **User creates a note/notepad tab**
2. **System retrieves current user** from `request.state.user` (set by middleware)
3. **System queries user's groups**:
   ```sql
   SELECT g.id 
   FROM user_groups ug 
   JOIN groups g ON ug.group_id = g.id 
   WHERE ug.user_id = ?
   ORDER BY CASE WHEN g.name = 'Admins' THEN 0 ELSE 1 END
   LIMIT 1
   ```
4. **System assigns content to that group**
5. **Content stays in that group** even if user changes groups later

### Group Priority:
- If user is in "Admins" group → content assigned to Admins
- Otherwise → content assigned to first group user belongs to
- If user has no groups → group_id is NULL

## Benefits

✅ **Automatic assignment**: No manual group selection needed
✅ **Persists correctly**: Content stays in group even if user changes groups
✅ **Privacy ready**: Database structure supports group-based filtering
✅ **Audit trail**: Can see which user created each piece of content

## Next Steps (Not Yet Implemented)

The database now tracks which group each piece of content belongs to, but the **GET endpoints don't yet filter** based on this. To complete group-based privacy:

### 1. Update Notes List Endpoint
```python
# Current: Shows all notes
SELECT * FROM notes

# Should be: Shows only notes from user's groups
SELECT n.* 
FROM notes n
INNER JOIN user_groups ug ON n.group_id = ug.group_id
WHERE ug.user_id = ?
```

### 2. Update Notepad List Endpoint
```python
# Current: Shows all tabs
SELECT * FROM pad_tabs

# Should be: Shows only tabs from user's groups
SELECT p.* 
FROM pad_tabs p
INNER JOIN user_groups ug ON p.group_id = ug.group_id
WHERE ug.user_id = ?
```

### 3. Update Journal List Endpoint
- Same pattern once journal database is implemented

## Testing

1. **Create a new note** as user in Admins group
   - Check: `SELECT * FROM notes` should show group_id = 2
   
2. **Create a new notepad tab** as user in Admins group
   - Check: `SELECT * FROM pad_tabs` should show group_id = 2
   
3. **Move user to different group**
   - Previous notes should still be in original group
   - New notes should be in new group

## Database Schema

### Notes Table
```sql
CREATE TABLE notes (
    id INTEGER PRIMARY KEY,
    content TEXT,
    ts DATETIME,
    user_id INTEGER,
    group_id INTEGER,
    updated_at DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (group_id) REFERENCES groups(id)
)
```

### Notepad Tabs Table
```sql
CREATE TABLE pad_tabs (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    content TEXT DEFAULT '',
    user_id INTEGER,
    group_id INTEGER,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (group_id) REFERENCES groups(id)
)
```

## Files Modified

1. ✅ `migrate_groups.py` - NEW: One-time migration script
2. ✅ `plugins/notes/plugin.py` - Updated add_note() function
3. ✅ `plugins/notepad/database.py` - Added user_id and group_id columns
4. ✅ `plugins/notepad/plugin.py` - Updated add_tab() function
5. ✅ `app_new/api/admin_new.py` - Fixed hashed_password column name

## Verification Commands

```powershell
# Check notes assignments
py -c "import sqlite3; conn = sqlite3.connect('data/cameronpad_dev.db'); cur = conn.cursor(); cur.execute('SELECT id, user_id, group_id FROM notes'); print(cur.fetchall())"

# Check notepad tab assignments
py -c "import sqlite3; conn = sqlite3.connect('data/cameronpad_dev.db'); cur = conn.cursor(); cur.execute('SELECT id, name, user_id, group_id FROM pad_tabs'); print(cur.fetchall())"

# Check user groups
py -c "import sqlite3; conn = sqlite3.connect('data/cameronpad_dev.db'); cur = conn.cursor(); cur.execute('SELECT u.id, u.username, g.name FROM users u JOIN user_groups ug ON u.id = ug.user_id JOIN groups g ON ug.group_id = g.id'); print(cur.fetchall())"
```
