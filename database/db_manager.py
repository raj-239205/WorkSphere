from flask_sqlalchemy import SQLAlchemy
from contextlib import contextmanager

# Central Flask-SQLAlchemy DB instance
db = SQLAlchemy()

class DatabaseManager:
    """
    Singleton Database Manager providing transaction scopes
    for SQLAlchemy ORM operations.
    """
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance
        
    @contextmanager
    def session_scope(self):
        """
        Transactional context manager. Commits on success,
        automatically rolls back on exceptions.
        """
        session = db.session
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
