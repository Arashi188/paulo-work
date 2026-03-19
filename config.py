import os
from datetime import timedelta

class Config:
    # Basic Flask config
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database configuration
    # Use SQLite for local development, PostgreSQL for production
    if os.environ.get('VERCEL_ENV') or os.environ.get('DATABASE_URL'):
        # Production (Vercel) - use PostgreSQL
        DATABASE_URL = os.environ.get('DATABASE_URL')
        if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
            DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
        SQLALCHEMY_DATABASE_URI = DATABASE_URL or 'postgresql://postgres:mFxwM5qnfYFABSD9@db.jhnpanznxoanclyrzvqx.supabase.co:5432/postgres'
        
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_size': 5,
            'pool_recycle': 280,
            'pool_pre_ping': True,
            'max_overflow': 10,
            'connect_args': {
                'connect_timeout': 10,
                'sslmode': 'require'
            }
        }
    else:
        # Local development - use SQLite
        SQLALCHEMY_DATABASE_URI = 'sqlite:///ecommerce.db'
        SQLALCHEMY_ENGINE_OPTIONS = {}
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session config
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    SESSION_COOKIE_SECURE = False  # Set to True only in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Cloudinary config
    CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME', 'dapuaw0u6')
    CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY', '738952696443951')
    CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET', 'CzRSL1UUAnGoOI1xnrc1NwlMIiU')
    
    # Admin settings
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@paulo-store.com')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'Admin123!')
    
    # WhatsApp settings
    WHATSAPP_NUMBER = os.environ.get('WHATSAPP_NUMBER', '2347088028747')
    
    # Security settings
    CSRF_ENABLED = True
    CSRF_SESSION_KEY = os.environ.get('CSRF_SESSION_KEY', 'csrf-secret-key')
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif']