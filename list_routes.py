"""
List all registered routes in the FastAPI app
"""
import sys
sys.path.insert(0, '.')

from app_new.main import create_app

app = create_app()

print("\n📋 Registered Routes:")
print("=" * 80)
for route in app.routes:
    if hasattr(route, 'methods'):
        methods = ', '.join(route.methods)
        print(f"{methods:10} {route.path}")
    else:
        print(f"{'MOUNT':10} {route.path}")
print("=" * 80)
