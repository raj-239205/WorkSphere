from services.base_service import BaseService
from repositories.department_repository import DepartmentRepository
from repositories.activity_log_repository import ActivityLogRepository
from exceptions.custom_exceptions import DepartmentNotFoundException
from models.department import Department
from models.activity_log import ActivityLog
from database.db_manager import DatabaseManager
from typing import List, Optional
import json

class DepartmentService(BaseService):
    """Department business logic service layer."""

    def __init__(self, department_repo: DepartmentRepository = None, activity_log_repo: ActivityLogRepository = None):
        self.department_repo = department_repo or DepartmentRepository()
        self.activity_log_repo = activity_log_repo or ActivityLogRepository()
        self.db_manager = DatabaseManager()

    def get_all_departments(self, include_inactive: bool = False) -> List[Department]:
        return self.department_repo.get_all(include_inactive)

    def get_department_by_id(self, department_id: int) -> Optional[Department]:
        return self.department_repo.get_by_id(department_id)

    def get_department_by_name(self, name: str) -> Optional[Department]:
        return self.department_repo.get_by_name(name)

    def create_department(self, department_name: str, manager_name: str) -> Department:
        """Creates a new Department. Enforces department name uniqueness."""
        with self.db_manager.session_scope():
            existing = self.department_repo.get_by_name(department_name)
            if existing:
                raise ValueError(f"Department '{department_name}' already exists.")

            dept = Department(department_name=department_name, manager_name=manager_name)
            created = self.department_repo.create(dept)

            # Log audit trail
            log = ActivityLog(
                user_id=None,
                action_type="Department Created",
                new_value=json.dumps(created.to_dict())
            )
            self.activity_log_repo.create(log)
            return created

    def update_department(self, department_id: int, department_name: str, manager_name: str) -> None:
        """Updates department details. Enforces name uniqueness excluding itself."""
        with self.db_manager.session_scope():
            dept = self.department_repo.get_by_id(department_id)
            if not dept:
                raise DepartmentNotFoundException(f"Department with ID {department_id} not found.")

            existing = self.department_repo.get_by_name(department_name)
            if existing and existing.department_id != int(department_id):
                raise ValueError(f"Department '{department_name}' already exists.")

            old_state = json.dumps(dept.to_dict())

            dept.department_name = department_name
            dept.manager_name = manager_name

            self.department_repo.update(dept)

            # Log audit trail
            log = ActivityLog(
                user_id=None,
                action_type="Department Updated",
                old_value=old_state,
                new_value=json.dumps(dept.to_dict())
            )
            self.activity_log_repo.create(log)

    def delete_department(self, department_id: int) -> None:
        """Soft-deletes department if it has no active employees."""
        with self.db_manager.session_scope():
            dept = self.department_repo.get_by_id(department_id)
            if not dept:
                raise DepartmentNotFoundException(f"Department with ID {department_id} not found.")

            # Check for active employees in department
            active_employees = [e for e in dept.employees if e.is_active]
            if len(active_employees) > 0:
                raise ValueError("Cannot delete department because it has active employees. Reassign employees first.")

            old_state = json.dumps(dept.to_dict())
            self.department_repo.delete(department_id)

            # Log audit trail
            log = ActivityLog(
                user_id=None,
                action_type="Department Deleted",
                old_value=old_state
            )
            self.activity_log_repo.create(log)

    def restore_department(self, department_id: int) -> None:
        """Restores soft-deleted department."""
        with self.db_manager.session_scope():
            dept = self.department_repo.get_by_id(department_id)
            if not dept:
                raise DepartmentNotFoundException(f"Department with ID {department_id} not found.")

            self.department_repo.restore(department_id)

            # Log audit trail
            log = ActivityLog(
                user_id=None,
                action_type="Department Restored",
                new_value=json.dumps(dept.to_dict())
            )
            self.activity_log_repo.create(log)
