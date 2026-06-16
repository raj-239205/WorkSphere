from database.db import DB
from models.user import User

class UserService:
    @staticmethod
    def get_user_by_id(user_id):
        query = "SELECT * FROM users WHERE user_id = ?"
        row = DB.execute_query(query, (user_id,), fetch_one=True)
        return User.from_row(row) if row else None

    @staticmethod
    def get_user_by_username(username):
        query = "SELECT * FROM users WHERE username = ?"
        row = DB.execute_query(query, (username,), fetch_one=True)
        return User.from_row(row) if row else None

    @staticmethod
    def get_user_by_employee_id(emp_id):
        query = "SELECT * FROM users WHERE emp_id = ?"
        row = DB.execute_query(query, (emp_id,), fetch_one=True)
        return User.from_row(row) if row else None

    @staticmethod
    def authenticate_user(username, password):
        """
        Authenticates user username and password. Returns User object if valid, else None.
        """
        user = UserService.get_user_by_username(username)
        if user and user.check_password(password):
            return user
        return None

    @staticmethod
    def create_user(username, password, role, emp_id=None):
        """
        Registers a new user, hashes password, and persists to DB.
        """
        # Validate unique username
        existing = UserService.get_user_by_username(username)
        if existing:
            raise ValueError(f"Username '{username}' is already taken.")

        if emp_id:
            # Validate that this employee is not already linked to another user
            existing_emp_user = UserService.get_user_by_employee_id(emp_id)
            if existing_emp_user:
                raise ValueError("This employee is already registered with a user account.")

        user = User(username=username, role=role, emp_id=emp_id)
        user.set_password(password)

        query = """
            INSERT INTO users (username, password, role, emp_id)
            VALUES (?, ?, ?, ?)
        """
        user_id = DB.execute_query(query, (user.username, user.password, user.role, user.emp_id))
        user.user_id = user_id
        return user
