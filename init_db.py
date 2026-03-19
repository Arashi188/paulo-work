# init_db.py
import os
import sys
from app import create_app, db
from app.models import User

print("=" * 50)
print("INITIALIZING DATABASE")
print("=" * 50)

app = create_app()

with app.app_context():
    # Create tables
    print("Creating database tables...")
    db.create_all()
    print("✅ Tables created successfully!")
    
    # Check if admin user exists
    admin = User.query.filter_by(is_admin=True).first()
    
    if not admin:
        # Create admin user
        from config import Config
        admin = User(
            username=Config.ADMIN_USERNAME,
            email=Config.ADMIN_EMAIL,
            is_admin=True
        )
        admin.set_password(Config.ADMIN_PASSWORD)
        db.session.add(admin)
        db.session.commit()
        print(f"✅ Admin user created: {Config.ADMIN_USERNAME}")
    else:
        print(f"✅ Admin user already exists: {admin.username}")
    
    print("\n" + "=" * 50)
    print("DATABASE INITIALIZATION COMPLETE")
    print("=" * 50)
    print("\nYou can now login at: http://127.0.0.1:5000/admin/login")
    print(f"Username: admin")
    print(f"Password: Admin123!")