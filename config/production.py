import os
from config import BaseConfig

class ProductionConfig(BaseConfig):
    ENV = 'production'
    DEBUG = False
    TESTING = False
    
    # Ensure secure secrets are enforced in production
    SECRET_KEY = os.environ.get('SECRET_KEY')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    
    # Secure Session Cookies
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    
    # Overwrite engine options for PostgreSQL in production
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_size": 10,
        "max_overflow": 20
    }
    
    # Database Configurations
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if not DATABASE_URL:
        raise ValueError("PRODUCTION ERROR: DATABASE_URL environment variable is not set!")
        
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    
    # Strict validation of configuration variables
    if not SECRET_KEY or SECRET_KEY == 'worksphere_secure_secret_key_12983719283':
        raise ValueError("PRODUCTION ERROR: SECRET_KEY environment variable is not securely set!")
        
    if not JWT_SECRET_KEY or JWT_SECRET_KEY == 'jwt_secret_key_worksphere_8923749823':
        raise ValueError("PRODUCTION ERROR: JWT_SECRET_KEY environment variable is not securely set!")
