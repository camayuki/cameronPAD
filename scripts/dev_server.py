"""
Development server script
Easy way to run CameronPAD locally with auto-reload
"""
import os
import sys
import asyncio
from pathlib import Path

# Add the app to Python path
sys.path.append(str(Path(__file__).parent.parent))

def create_admin_user():
    """Create admin user if it doesn't exist"""
    import sqlite3
    import hashlib
    
    db_path = "data/cameronpad_dev.db"
    
    # Create database and tables if they don't exist
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            full_name TEXT,
            role TEXT DEFAULT 'user',
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    """)
    
    # Check if admin user exists
    cursor.execute("SELECT id FROM users WHERE username = 'admin'")
    if cursor.fetchone() is None:
        # Create admin user with bcrypt-like hash (simplified for development)
        import bcrypt
        password = "admin123!"
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        cursor.execute("""
            INSERT INTO users (username, email, hashed_password, full_name, role, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("admin", "admin@cameronpad.dev", hashed.decode('utf-8'), "Administrator", "admin", 1))
        
        print("✅ Admin user created: admin / admin123!")
    
    # Check if test user exists
    cursor.execute("SELECT id FROM users WHERE username = 'testuser'")
    if cursor.fetchone() is None:
        import bcrypt
        password = "test123!"
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        cursor.execute("""
            INSERT INTO users (username, email, hashed_password, full_name, role, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("testuser", "test@cameronpad.dev", hashed.decode('utf-8'), "Test User", "user", 1))
        
        print("✅ Test user created: testuser / test123!")
    
    conn.commit()
    conn.close()

def run_dev_server():
    """Run development server with auto-reload"""
    print("🚀 Starting CameronPAD Development Server...")
    print("🌐 Local URL: http://127.0.0.1:8000")
    print("📱 Network URL: http://localhost:8000") 
    print("🔧 Admin Panel: http://127.0.0.1:8000/admin")
    print("📚 API Docs: http://127.0.0.1:8000/docs")
    print("⚡ Auto-reload enabled - changes will be detected automatically")
    print("🛑 Press Ctrl+C to stop the server")
    print("-" * 60)
    
    # Ensure directories exist
    Path("data").mkdir(exist_ok=True)
    Path("logs").mkdir(exist_ok=True)
    
    # Create admin user
    try:
        create_admin_user()
    except Exception as e:
        print(f"⚠️  Could not create admin user: {e}")
        print("   You may need to install bcrypt: pip install bcrypt")
    
    # Set environment to development
    os.environ["ENVIRONMENT"] = "development"
    
    # Try to import and run uvicorn
    try:
        import uvicorn
        
        # Run the server
        uvicorn.run(
            "app_new.main:app",
            host="127.0.0.1",
            port=8000,
            reload=True,
            reload_dirs=["app_new", "plugins", "templates"],
            env_file=".env.dev",
            log_level="debug"
        )
    except ImportError:
        print("❌ uvicorn not found. Please install it:")
        print("   pip install uvicorn")
    except ImportError:
        print("❌ FastAPI application not found. Please check your app_new/main.py file")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

if __name__ == "__main__":
    run_dev_server()