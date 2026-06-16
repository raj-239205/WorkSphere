import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'smart_erp_secure_secret_key_12983719283')
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATABASE_PATH = os.path.join(BASE_DIR, 'database', 'erp.db')
    
    # Session lifetime, cookie settings, etc. can go here
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
