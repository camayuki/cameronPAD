"""
Create admin user for CameronPAD
"""
import sqlite3
import bcrypt

# Connect to database
conn = sqlite3.connect('data/cameronpad_dev.db')
cursor = conn.cursor()

# Check current schema
cursor.execute("PRAGMA table_info(users)")
columns = {col[1] for col in cursor.fetchall()}
print(f"Current columns: {columns}")

# Hash the password
password = "admin123!"
password_bytes = password.encode('utf-8')
salt = bcrypt.gensalt()
hashed_password = bcrypt.hashpw(password_bytes, salt).decode('utf-8')

try:
    if 'password_hash' in columns and 'is_admin' in columns:
        # New schema
        cursor.execute("""
            INSERT OR REPLACE INTO users (username, email, password_hash, is_active, is_admin)
            VALUES (?, ?, ?, ?, ?)
        """, ('admin', 'admin@cameronpad.local', hashed_password, 1, 1))
        print("✅ Created admin user with new schema (password_hash, is_admin)")
    
    elif 'hashed_password' in columns and 'role' in columns:
        # Old schema
        cursor.execute("""
            INSERT OR REPLACE INTO users (username, email, hashed_password, role, is_active)
            VALUES (?, ?, ?, ?, ?)
        """, ('admin', 'admin@cameronpad.local', hashed_password, 'admin', 1))
        print("✅ Created admin user with old schema (hashed_password, role)")
    
    else:
        print("❌ Unknown schema!")
        print(f"Columns: {columns}")
    
    conn.commit()
    
    # Verify the user was created
    if 'password_hash' in columns:
        cursor.execute("SELECT id, username, email, is_active, is_admin FROM users WHERE username = 'admin'")
    else:
        cursor.execute("SELECT id, username, email, is_active, role FROM users WHERE username = 'admin'")
    
    result = cursor.fetchone()
    if result:
        print(f"\n✅ Admin user verified:")
        print(f"   ID: {result[0]}")
        print(f"   Username: {result[1]}")
        print(f"   Email: {result[2]}")
        print(f"   Active: {result[3]}")
        print(f"   Admin/Role: {result[4]}")
        print(f"\n🔑 Login credentials:")
        print(f"   Username: admin")
        print(f"   Password: admin123!")
    else:
        print("❌ Failed to create admin user")

except Exception as e:
    print(f"❌ Error: {e}")
    conn.rollback()

finally:
    conn.close()
