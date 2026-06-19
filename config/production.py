import os
from config import BaseConfig

class ProductionConfig(BaseConfig):
    ENV = 'production'
    
    # Ensure secure secrets are enforced in production
    SECRET_KEY = os.environ.get('SECRET_KEY')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    
    # Secure Session Cookies
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    
    if not SECRET_KEY or SECRET_KEY == 'worksphere_secure_secret_key_12983719283':
        raise ValueError("PRODUCTION ERROR: SECRET_KEY environment variable is not securely set!")
