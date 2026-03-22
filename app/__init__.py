import os
import sys
from flask import Flask, render_template, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_cors import CORS
import cloudinary
import cloudinary.uploader
import cloudinary.api
from config import Config

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()

def create_app(config_class=Config):
    app = Flask(
        __name__,
        template_folder='../templates',
        static_folder='../static',
        static_url_path='/static'
    )

    app.config.from_object(config_class)

    # ✅ Proper secret key handling (NO Vercel logic)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-me')

    # ✅ Fix database URL format (important for PostgreSQL)
    database_url = app.config.get('SQLALCHEMY_DATABASE_URI')
    if database_url and database_url.startswith('postgres://'):
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url.replace('postgres://', 'postgresql://', 1)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # ✅ Enable CORS (for future flexibility)
    CORS(app)

    # Configure Cloudinary
    cloudinary.config(
        cloud_name=app.config.get('CLOUDINARY_CLOUD_NAME'),
        api_key=app.config.get('CLOUDINARY_API_KEY'),
        api_secret=app.config.get('CLOUDINARY_API_SECRET'),
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

    @app.errorhandler(400)
    def bad_request_error(error):
        flash('Bad request. Please check your input.', 'danger')
        return redirect(url_for('main.index'))

    # ✅ SAFE: Only initialize DB locally (NOT on Render)
    if not os.environ.get("RENDER"):
        with app.app_context():
            try:
                from sqlalchemy import text
                db.session.execute(text('SELECT 1'))
                db.session.commit()

                db.create_all()
                print("✅ Local database initialized")

            except Exception as e:
                print(f"⚠️ DB init warning: {e}")

    return app