# test_local.py
import os
import sys
from sqlalchemy import create_engine, text

print("=" * 50)
print("TESTING LOCAL SETUP")
print("=" * 50)

# Test 1: Check if we can import the app
try:
    from app import create_app, db
    from app.models import User, Product, Order
    print("✅ Successfully imported app modules")
except Exception as e:
    print(f"❌ Failed to import app modules: {e}")
    sys.exit(1)

# Test 2: Check database connection
try:
    # Get database URL from config
    from config import Config
    db_url = Config.SQLALCHEMY_DATABASE_URI
    print(f"\nDatabase URL: {db_url}")
    
    # Try to connect
    engine = create_engine(db_url)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
        print("✅ Successfully connected to database")
except Exception as e:
    print(f"❌ Database connection failed: {e}")

# Test 3: Try to create app and tables
try:
    print("\nCreating Flask app...")
    app = create_app()
    with app.app_context():
        # Try to create tables
        db.create_all()
        print("✅ Tables created/verified successfully")
        
        # Check if admin user exists
        admin = User.query.filter_by(is_admin=True).first()
        if admin:
            print(f"✅ Admin user exists: {admin.username}")
        else:
            print("⚠️ No admin user found - will be created on first run")
except Exception as e:
    print(f"❌ App creation failed: {e}")

print("\n" + "=" * 50)