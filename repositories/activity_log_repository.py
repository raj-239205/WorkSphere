from database.db_manager import db
from repositories.base_repository import BaseRepository
from models.activity_log import ActivityLog
from typing import List, Optional

class ActivityLogRepository(BaseRepository):
    """ActivityLog data access repository using SQLAlchemy ORM."""

    def get_by_id(self, entity_id: int) -> Optional[ActivityLog]:
        return db.session.get(ActivityLog, entity_id)

    def get_all(self) -> List[ActivityLog]:
        return db.session.query(ActivityLog).order_by(ActivityLog.timestamp.desc()).all()

    def get_paginated(self, page: int = 1, limit: int = 20, search_query: str = None) -> tuple:
        """Returns a tuple of (items, total_count)."""
        query = db.session.query(ActivityLog)
        
        if search_query:
            search_pattern = f"%{search_query}%"
            query = query.filter(
                (ActivityLog.action_type.like(search_pattern)) |
                (ActivityLog.ip_address.like(search_pattern)) |
                (ActivityLog.old_value.like(search_pattern)) |
                (ActivityLog.new_value.like(search_pattern))
            )
            
        total = query.count()
        items = query.order_by(ActivityLog.timestamp.desc()).offset((page - 1) * limit).limit(limit).all()
        return items, total

    def create(self, entity: ActivityLog) -> ActivityLog:
        db.session.add(entity)
        db.session.flush()
        return entity

    def update(self, entity: ActivityLog) -> None:
        db.session.merge(entity)

    def delete(self, entity_id: int) -> None:
        log = self.get_by_id(entity_id)
        if log:
            db.session.delete(log)
