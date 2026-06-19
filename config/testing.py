from config import BaseConfig

class TestingConfig(BaseConfig):
    TESTING = True
    DEBUG = True
    ENV = 'testing'
    
    # Fast in-memory SQLite database for test suites
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    
    # Disable rate limits and security delays during tests
    RATELIMIT_ENABLED = False
