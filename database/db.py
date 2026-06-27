import sqlite3
import os
from config import Config

class DB:
    @staticmethod
    def get_connection():
        """
        Creates and returns a connection to the database.
        Ensures foreign keys are enabled and rows can be accessed as dictionaries.
        """
        # Ensure the directory exists
        db_dir = os.path.dirname(Config.DATABASE_PATH)
        if not os.environ.get("VERCEL") and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            
        if os.environ.get("VERCEL"):
            conn = sqlite3.connect(":memory:")
        else:
            conn = sqlite3.connect(Config.DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    class ConnectionContext:
        """
        A context manager that yields a connection, commits on success, 
        and rolls back transactions on exceptions.
        """
        def __init__(self):
            self.conn = None

        def __enter__(self):
            self.conn = DB.get_connection()
            return self.conn

        def __exit__(self, exc_type, exc_val, exc_tb):
            if self.conn:
                if exc_type is not None:
                    # An error occurred, rollback
                    self.conn.rollback()
                else:
                    self.conn.commit()
                self.conn.close()

    @classmethod
    def session(cls):
        """
        Usage:
        with DB.session() as conn:
            conn.execute(...)
        """
        return cls.ConnectionContext()

    @classmethod
    def execute_query(cls, query, params=(), fetch_all=False, fetch_one=False):
        """
        Utility method to execute a query and return results.
        Automatically handles connection lifecycle.
        """
        with cls.session() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            if fetch_all:
                return [dict(row) for row in cursor.fetchall()]
            if fetch_one:
                row = cursor.fetchone()
                return dict(row) if row else None
            return cursor.lastrowid
