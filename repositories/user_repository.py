from database.db_manager import db
from repositories.base_repository import BaseRepository
from models.user import User
from typing import List, Optional

class UserRepository(BaseRepository):
    """User data access repository using SQLAlchemy ORM."""
    
    def get_by_id(self, entity_id: int) -> Optional[User]:
        return db.session.get(User, entity_id)

    def get_by_username(self, username: str) -> Optional[User]:
        return db.session.query(User).filter(User.username == username).first()

    def get_all(self) -> List[User]:
        return db.session.query(User).all()

    def create(self, entity: User) -> User:
        db.session.add(entity)
        db.session.flush()  # Flushes to DB to obtain auto-increment ID
        return entity

    def update(self, entity: User) -> None:
        db.session.merge(entity)

    def delete(self, entity_id: int) -> None:
        user = self.get_by_id(entity_id)
        if user:
            # Soft delete configuration
            user.is_active = False
            db.session.add(user)
            
    def restore(self, entity_id: int) -> None:
        user = self.get_by_id(entity_id)
        if user:
            user.is_active = True
            db.session.add(user)
