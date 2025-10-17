"""
Development setup script
Run this to initialize your local development environment
"""
import asyncio
import os
import sys
from pathlib import Path

# Add the app to Python path
sys.path.append(str(Path(__file__).parent.parent))

async def setup_development():
    """Setup development environment"""
    print("🚀 Setting up CameronPAD development environment...")
    
    # Create necessary directories
    directories = [
        "data",
        "data/uploads", 
        "logs",
        "config/environments"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    # Create development config
    dev_config = """
# Development Configuration
app:
  name: "CameronPAD"
  environment: "development"
  debug: true
  host: "127.0.0.1"
  port: 8000

database:
  url: "sqlite+aiosqlite:///./data/cameronpad_dev.db"
  echo: true

security:
  secret_key: "dev-secret-key-change-in-production"
  algorithm: "HS256"
  access_token_expire_minutes: 1440

logging:
  level: "DEBUG"
  file: "./logs/cameronpad_dev.log"

plugins:
  auto_discover: true
  directory: "./plugins"

cache:
  backend: "memory"
  default_ttl: 300
"""
    
    config_file = Path("config/environments/development.yaml")
    config_file.parent.mkdir(parents=True, exist_ok=True)
    config_file.write_text(dev_config)
    print("✅ Development configuration created")
    
    # Create .env.dev file
    env_content = """# Development Environment Variables
ENVIRONMENT=development
DEBUG=true
DATABASE_URL=sqlite+aiosqlite:///./data/cameronpad_dev.db
SECRET_KEY=dev-secret-key-change-in-production
LOG_LEVEL=DEBUG
HOST=127.0.0.1
PORT=8000
"""
    
    env_file = Path(".env.dev")
    env_file.write_text(env_content)
    print("✅ Environment file created")
    
    print("\n🎉 Development environment setup complete!")
    print("📚 Next steps:")
    print("   1. Install dependencies: pip install fastapi uvicorn jinja2 python-multipart sqlalchemy aiosqlite pydantic python-dotenv")
    print("   2. Run development server: python scripts/dev_server.py")
    print("   3. Access the site: http://127.0.0.1:8000")
    print("\n👤 Default login will be created when you first run the server:")
    print("   Username: admin")
    print("   Password: admin123!")

if __name__ == "__main__":
    asyncio.run(setup_development())