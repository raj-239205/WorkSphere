from services.base_service import BaseService
from repositories.user_repository import UserRepository
from repositories.activity_log_repository import ActivityLogRepository
from models.user import User, Admin, HR, Employee
from models.activity_log import ActivityLog
from database.db_manager import DatabaseManager
from typing import List, Optional
import json

class UserService(BaseService):
    """User business logic service layer."""

    def __init__(self, user_repo: UserRepository = None, activity_log_repo: ActivityLogRepository = None):
        self.user_repo = user_repo or UserRepository()
        self.activity_log_repo = activity_log_repo or ActivityLogRepository()
        self.db_manager = DatabaseManager()

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        return self.user_repo.get_by_id(user_id)

    def get_user_by_username(self, username: str) -> Optional[User]:
        return self.user_repo.get_by_username(username)

    def authenticate_user(self, username: str, password: str, ip_address: str = None) -> Optional[User]:
        """Authenticates user username and password. Logs the login attempt."""
        user = self.get_user_by_username(username)
        if user and user.is_active and user.check_password(password):
            with self.db_manager.session_scope():
                log = ActivityLog(
                    user_id=user.user_id,
                    action_type="Login Success",
                    ip_address=ip_address
                )
                self.activity_log_repo.create(log)
            return user
            
        if user:
            with self.db_manager.session_scope():
                log = ActivityLog(
                    user_id=user.user_id,
                    action_type="Login Failed (Incorrect Password)",
                    ip_address=ip_address
                )
                self.activity_log_repo.create(log)
        return None

    def log_logout(self, user_id: int, ip_address: str = None) -> None:
        """Logs user logout event."""
        with self.db_manager.session_scope():
            log = ActivityLog(
                user_id=user_id,
                action_type="Logout",
                ip_address=ip_address
            )
            self.activity_log_repo.create(log)

    def create_user(self, username: str, role: str, password: str = None, **kwargs) -> User:
        """Creates and registers a new User / Admin / HR / Employee role."""
        with self.db_manager.session_scope():
            existing = self.user_repo.get_by_username(username)
            if existing:
                raise ValueError(f"Username '{username}' is already taken.")

            # Create specific polymorphic subclass instance
            if role == 'Admin':
                user = Admin(username=username)
            elif role == 'HR':
                user = HR(username=username)
            elif role == 'Employee':
                user = Employee(
                    username=username,
                    name=kwargs.get('name'),
                    email=kwargs.get('email'),
                    phone=kwargs.get('phone'),
                    department_id=kwargs.get('department_id'),
                    salary=kwargs.get('salary', 0.0),
                    designation=kwargs.get('designation')
                )
            else:
                user = User(username=username, role=role)

            if password:
                user.password = password  # Calls setter validation
            else:
                user.password = "WorkSphere123"  # default password

            created_user = self.user_repo.create(user)
            
            # Log user creation activity
            log = ActivityLog(
                user_id=None,  # Or system/admin ID
                action_type=f"User Created: {role}",
                new_value=json.dumps({"username": username, "role": role})
            )
            self.activity_log_repo.create(log)
            
            return created_user

    def get_all_users(self) -> List[User]:
        return self.user_repo.get_all()
        
    def log_api_access(self, user_id: int, action_type: str, ip_address: str = None, details: str = None) -> None:
        """Helper to log general API access events."""
        with self.db_manager.session_scope():
            log = ActivityLog(
                user_id=user_id,
                action_type=action_type,
                ip_address=ip_address,
                new_value=details
            )
            self.activity_log_repo.create(log)
