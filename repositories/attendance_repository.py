from database.db_manager import db
from repositories.base_repository import BaseRepository
from models.attendance import Attendance
from typing import List, Optional

class AttendanceRepository(BaseRepository):
    """Attendance data access repository using SQLAlchemy ORM."""

    def get_by_id(self, entity_id: int) -> Optional[Attendance]:
        return db.session.get(Attendance, entity_id)

    def get_by_emp_and_date(self, emp_id: int, date: str) -> Optional[Attendance]:
        return db.session.query(Attendance).filter(
            Attendance.emp_id == emp_id,
            Attendance.date == date
        ).first()

    def get_all(self, include_inactive: bool = False) -> List[Attendance]:
        query = db.session.query(Attendance)
        if not include_inactive:
            query = query.filter(Attendance.is_active == True)
        return query.order_by(Attendance.date.desc()).all()

    def get_records(self, emp_id: int = None, date: str = None, include_inactive: bool = False) -> List[Attendance]:
        query = db.session.query(Attendance)
        if not include_inactive:
            query = query.filter(Attendance.is_active == True)
        if emp_id:
            query = query.filter(Attendance.emp_id == emp_id)
        if date:
            query = query.filter(Attendance.date == date)
        return query.order_by(Attendance.date.desc()).all()

    def create(self, entity: Attendance) -> Attendance:
        db.session.add(entity)
        db.session.flush()
        return entity

    def update(self, entity: Attendance) -> None:
        db.session.merge(entity)

    def delete(self, entity_id: int) -> None:
        record = self.get_by_id(entity_id)
        if record:
            record.is_active = False
            db.session.add(record)

    def restore(self, entity_id: int) -> None:
        record = self.get_by_id(entity_id)
        if record:
            record.is_active = True
            db.session.add(record)
            
    def get_recent(self, limit: int = 5) -> List[Attendance]:
        return db.session.query(Attendance).filter(
            Attendance.is_active == True
        ).order_by(Attendance.date.desc(), Attendance.attendance_id.desc()).limit(limit).all()
