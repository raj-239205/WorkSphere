from abc import ABC, abstractmethod
from typing import Any, List

class BaseRepository(ABC):
    """Abstract Base Repository enforcing standard CRUD interfaces."""
    
    @abstractmethod
    def get_by_id(self, entity_id: Any) -> Any:
        """Fetch a single record by ID."""
        pass
        
    @abstractmethod
    def get_all(self) -> List[Any]:
        """Fetch all records."""
        pass
        
    @abstractmethod
    def create(self, entity: Any) -> Any:
        """Persist a new entity record."""
        pass
        
    @abstractmethod
    def update(self, entity: Any) -> None:
        """Update an existing entity record."""
        pass
        
    @abstractmethod
    def delete(self, entity_id: Any) -> None:
        """Permanently or soft-delete a record."""
        pass
