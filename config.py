import os
from datetime import timedelta

class Config:
    # Basic Flask config
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')
    
    # Database - Supabase configuration with CORRECT hostname
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 
        'postgresql://postgres:mFxwM5qnfYFABSD9@db.jhnpanznxoanclyrzvqx.supabase.co:5432/postgres'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Add these settings for better PostgreSQL connection handling
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 280,
        'pool_pre_ping': True,
        'max_overflow': 20
    }
    
    # Session config
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Cloudinary config - your credentials
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