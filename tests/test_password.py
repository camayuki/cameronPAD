"""
Test password verification
"""
import sqlite3
import bcrypt
from passlib.context import CryptContext

# Connect to database
conn = sqlite3.connect('data/cameronpad_dev.db')
cursor = conn.cursor()

# Get admin user
cursor.execute("SELECT id, username, hashed_password FROM users WHERE username = 'admin'")
result = cursor.fetchone()

if result:
    user_id, username, stored_hash = result
    print(f"✅ Found user: {username} (ID: {user_id})")
    print(f"📝 Stored hash: {stored_hash[:50]}...")
    
    # Test password
    test_password = "admin123!"
    
    # Method 1: Direct bcrypt
    try:
        password_bytes = test_password.encode('utf-8')
        stored_hash_bytes = stored_hash.encode('utf-8')
        if bcrypt.checkpw(password_bytes, stored_hash_bytes):
            print("✅ Method 1 (bcrypt.checkpw): Password matches!")
        else:
            print("❌ Method 1 (bcrypt.checkpw): Password does NOT match")
    except Exception as e:
        print(f"❌ Method 1 error: {e}")
    
    # Method 2: Passlib
    try:
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        if pwd_context.verify(test_password, stored_hash):
            print("✅ Method 2 (passlib): Password matches!")
        else:
            print("❌ Method 2 (passlib): Password does NOT match")
    except Exception as e:
        print(f"❌ Method 2 error: {e}")
else:
    print("❌ Admin user not found!")

conn.close()
