from services.base_service import BaseService
from repositories.employee_repository import EmployeeRepository
from repositories.activity_log_repository import ActivityLogRepository
from exceptions.custom_exceptions import EmployeeNotFoundException
from models.user import Employee
from models.activity_log import ActivityLog
from database.db_manager import DatabaseManager
from typing import List, Optional
import json

class EmployeeService(BaseService):
    """Employee business logic service layer."""

    def __init__(self, employee_repo: EmployeeRepository = None, activity_log_repo: ActivityLogRepository = None):
        self.employee_repo = employee_repo or EmployeeRepository()
        self.activity_log_repo = activity_log_repo or ActivityLogRepository()
        self.db_manager = DatabaseManager()

    def get_all_employees(self, search_query: str = None, department_id: int = None, include_inactive: bool = False) -> List[Employee]:
        return self.employee_repo.get_all(search_query, department_id, include_inactive)

    def get_employee_by_id(self, emp_id: int) -> Optional[Employee]:
        return self.employee_repo.get_by_id(emp_id)

    def get_employee_by_email(self, email: str) -> Optional[Employee]:
        return self.employee_repo.get_by_email(email)

    def create_employee(self, name: str, email: str, phone: str, department_id: int, 
                        salary: float, designation: str, username: str = None, password: str = None) -> Employee:
        """Creates a new Employee record. Links it to a User entity automatically via Joined Table Inheritance."""
        with self.db_manager.session_scope():
            # Validate unique email
            existing = self.employee_repo.get_by_email(email)
            if existing:
                raise ValueError(f"An employee with email '{email}' already exists.")

            # Generate username from email if not provided
            if not username:
                username = email.split('@')[0]

            from repositories.user_repository import UserRepository
            user_repo = UserRepository()
            existing_user = user_repo.get_by_username(username)
            if existing_user:
                username = email  # Fallback to unique email if username is taken

            emp = Employee(
                username=username,
                name=name,
                email=email,
                phone=phone,
                department_id=department_id,
                salary=salary,  # Validation in setter
                designation=designation
            )
            emp.password = password or "WorkSphere123"  # default password
            
            created = self.employee_repo.create(emp)
            
            # Log audit trail
            log = ActivityLog(
                user_id=None,
                action_type="Employee Created",
                new_value=json.dumps(created.to_dict())
            )
            self.activity_log_repo.create(log)
            return created

    def update_employee(self, emp_id: int, name: str, email: str, phone: str, 
                        department_id: int, salary: float, designation: str) -> None:
        """Updates Employee details. Performs validation checks on inputs."""
        with self.db_manager.session_scope():
            emp = self.employee_repo.get_by_id(emp_id)
            if not emp:
                raise EmployeeNotFoundException(f"Employee with ID {emp_id} not found.")

            existing = self.employee_repo.get_by_email(email)
            if existing and existing.user_id != emp_id:
                raise ValueError(f"An employee with email '{email}' already exists.")

            old_state = json.dumps(emp.to_dict())

            emp.name = name
            emp.email = email
            emp.phone = phone
            emp.department_id = department_id
            emp.salary = salary  # setter validation triggers here
            emp.designation = designation

            self.employee_repo.update(emp)

            # Log audit trail
            log = ActivityLog(
                user_id=None,
                action_type="Employee Updated",
                old_value=old_state,
                new_value=json.dumps(emp.to_dict())
            )
            self.activity_log_repo.create(log)

    def delete_employee(self, emp_id: int) -> None:
        """Soft-deletes employee by marking is_active = False."""
        with self.db_manager.session_scope():
            emp = self.employee_repo.get_by_id(emp_id)
            if not emp:
                raise EmployeeNotFoundException(f"Employee with ID {emp_id} not found.")

            old_state = json.dumps(emp.to_dict())
            self.employee_repo.delete(emp_id)

            # Log audit trail
            log = ActivityLog(
                user_id=None,
                action_type="Employee Deleted",
                old_value=old_state
            )
            self.activity_log_repo.create(log)

    def restore_employee(self, emp_id: int) -> None:
        """Restores soft-deleted employee by marking is_active = True."""
        with self.db_manager.session_scope():
            emp = self.employee_repo.get_by_id(emp_id)
            if not emp:
                raise EmployeeNotFoundException(f"Employee with ID {emp_id} not found.")

            self.employee_repo.restore(emp_id)

            # Log audit trail
            log = ActivityLog(
                user_id=None,
                action_type="Employee Restored",
                new_value=json.dumps(emp.to_dict())
            )
            self.activity_log_repo.create(log)
