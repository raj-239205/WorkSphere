from database.db_manager import db
from repositories.base_repository import BaseRepository
from models.department import Department
from typing import List, Optional

class DepartmentRepository(BaseRepository):
    """Department data access repository using SQLAlchemy ORM."""

    def get_by_id(self, entity_id: int) -> Optional[Department]:
        return db.session.get(Department, entity_id)

    def get_by_name(self, name: str) -> Optional[Department]:
        return db.session.query(Department).filter(Department.department_name == name).first()

    def get_all(self, include_inactive: bool = False) -> List[Department]:
        query = db.session.query(Department)
        if not include_inactive:
            query = query.filter(Department.is_active == True)
        return query.order_by(Department.department_name.asc()).all()

    def create(self, entity: Department) -> Department:
        db.session.add(entity)
        db.session.flush()
        return entity

    def update(self, entity: Department) -> None:
        db.session.merge(entity)

    def delete(self, entity_id: int) -> None:
        dept = self.get_by_id(entity_id)
        if dept:
            dept.is_active = False
            db.session.add(dept)

    def restore(self, entity_id: int) -> None:
        dept = self.get_by_id(entity_id)
        if dept:
            dept.is_active = True
            db.session.add(dept)
