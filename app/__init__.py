import os
import sys
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
import cloudinary
import cloudinary.uploader
import cloudinary.api
from config import Config

# Add the parent directory to path for Vercel
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()

def create_app(config_class=Config):
    app = Flask(__name__, 
                template_folder='../templates',
                static_folder='../static',
                static_url_path='/static')
    app.config.from_object(config_class)
    
    # Ensure secret key is set
    if not app.config['SECRET_KEY'] or app.config['SECRET_KEY'] == 'your-secret-key-change-this-in-production':
        app.config['SECRET_KEY'] = os.urandom(24).hex()
        print("⚠️ Warning: Using a random secret key. Set SECRET_KEY environment variable for production.")
    
    # Handle database URL for Vercel (ensure it uses the correct format)
    database_url = app.config['SQLALCHEMY_DATABASE_URI']
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    
    # Configure Cloudinary with your credentials
    cloudinary.config(
        cloud_name=app.config['CLOUDINARY_CLOUD_NAME'],
        api_key=app.config['CLOUDINARY_API_KEY'],
        api_secret=app.config['CLOUDINARY_API_SECRET'],
        secure=True
    )
    
    # Configure login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    login_manager.session_protection = 'strong'
    
    # Register blueprints
    from app.routes import main_bp
    from app.admin import admin_bp
    from app.auth import auth_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(413)
    def too_large(error):
        return 'File is too large. Maximum size is 16MB.', 413
    
    # Create tables and admin user (only in development or first run)
    with app.app_context():
        try:
            # Check if database is accessible
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            db.session.commit()
            
            # Create all tables
            db.create_all()
            print("✅ Database tables created successfully!")
            
            # Create admin user if not exists
            from app.models import User
            admin = User.query.filter_by(is_admin=True).first()
            
            if not admin:
                admin = User(
                    username=app.config['ADMIN_USERNAME'],
                    email=app.config['ADMIN_EMAIL'],
                    is_admin=True
                )
                admin.set_password(app.config['ADMIN_PASSWORD'])
                db.session.add(admin)
                db.session.commit()
                print(f"✅ Admin user created: {app.config['ADMIN_USERNAME']}")
            else:
                print(f"✅ Admin user already exists: {admin.username}")
                
        except Exception as e:
            print(f"⚠️ Database initialization warning: {e}")
            print("This is normal on first deployment - tables will be created by SQLAlchemy")
    
    return app