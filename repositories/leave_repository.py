from database.db_manager import db
from repositories.base_repository import BaseRepository
from models.leave import LeaveRequest
from typing import List, Optional

class LeaveRepository(BaseRepository):
    """Leave Request data access repository using SQLAlchemy ORM."""

    def get_by_id(self, entity_id: int) -> Optional[LeaveRequest]:
        return db.session.get(LeaveRequest, entity_id)

    def get_all(self, include_inactive: bool = False) -> List[LeaveRequest]:
        query = db.session.query(LeaveRequest)
        if not include_inactive:
            query = query.filter(LeaveRequest.is_active == True)
        return query.order_by(LeaveRequest.start_date.desc()).all()

    def get_records(self, emp_id: int = None, status: str = None, include_inactive: bool = False) -> List[LeaveRequest]:
        query = db.session.query(LeaveRequest)
        if not include_inactive:
            query = query.filter(LeaveRequest.is_active == True)
        if emp_id:
            query = query.filter(LeaveRequest.emp_id == emp_id)
        if status:
            query = query.filter(LeaveRequest.status == status)
        return query.order_by(LeaveRequest.start_date.desc()).all()

    def create(self, entity: LeaveRequest) -> LeaveRequest:
        db.session.add(entity)
        db.session.flush()
        return entity

    def update(self, entity: LeaveRequest) -> None:
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

    def get_pending_count(self) -> int:
        return db.session.query(LeaveRequest).filter(
            LeaveRequest.status == 'Pending',
            LeaveRequest.is_active == True
        ).count()

    def get_recent(self, limit: int = 5) -> List[LeaveRequest]:
        return db.session.query(LeaveRequest).filter(
            LeaveRequest.is_active == True
        ).order_by(LeaveRequest.leave_id.desc()).limit(limit).all()

    def get_overlapping_requests(self, emp_id: int, start_date: str, end_date: str, exclude_leave_id: int = None) -> List[LeaveRequest]:
        query = db.session.query(LeaveRequest).filter(
            LeaveRequest.emp_id == emp_id,
            LeaveRequest.status != 'Rejected',
            LeaveRequest.is_active == True,
            LeaveRequest.start_date <= end_date,
            LeaveRequest.end_date >= start_date
        )
        if exclude_leave_id:
            query = query.filter(LeaveRequest.leave_id != exclude_leave_id)
        return query.all()
