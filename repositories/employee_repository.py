from database.db_manager import db
from repositories.base_repository import BaseRepository
from models.user import Employee
from typing import List, Optional

class EmployeeRepository(BaseRepository):
    """Employee data access repository using SQLAlchemy ORM."""

    def get_by_id(self, entity_id: int) -> Optional[Employee]:
        # Fetch employee by ID (user_id)
        return db.session.get(Employee, entity_id)

    def get_by_email(self, email: str) -> Optional[Employee]:
        return db.session.query(Employee).filter(Employee.email == email).first()

    def get_all(self, search_query: str = None, department_id: int = None, include_inactive: bool = False) -> List[Employee]:
        query = db.session.query(Employee)
        
        if not include_inactive:
            query = query.filter(Employee.is_active == True)
            
        if department_id:
            query = query.filter(Employee.department_id == department_id)
            
        if search_query:
            search_pattern = f"%{search_query}%"
            query = query.filter(
                (Employee.name.like(search_pattern)) |
                (Employee.email.like(search_pattern)) |
                (Employee.designation.like(search_pattern))
            )
            
        return query.order_by(Employee.name.asc()).all()

    def create(self, entity: Employee) -> Employee:
        db.session.add(entity)
        db.session.flush()
        return entity

    def update(self, entity: Employee) -> None:
        db.session.merge(entity)

    def delete(self, entity_id: int) -> None:
        employee = self.get_by_id(entity_id)
        if employee:
            employee.is_active = False
            db.session.add(employee)

    def restore(self, entity_id: int) -> None:
        employee = self.get_by_id(entity_id)
        if employee:
            employee.is_active = True
            db.session.add(employee)
