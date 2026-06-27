import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class BaseConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'worksphere_secure_secret_key_12983719283')
    
    # Database Configurations
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f"sqlite:///{os.path.join(BASE_DIR, 'database', 'erp.db')}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300
    }
    
    # JWT Configurations
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt_secret_key_worksphere_8923749823')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_TOKEN_LOCATION = ['headers', 'cookies']
    JWT_COOKIE_CSRF_PROTECT = False  # Set to True in fully secured production setups
    
    # Rate Limiter
    RATELIMIT_HEADERS_ENABLED = True
    RATELIMIT_STORAGE_URI = "memory://"
    
    # Environment status
    DEBUG = False
    TESTING = False
