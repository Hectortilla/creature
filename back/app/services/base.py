"""
Base Service Classes

Provides common CRUD operations and simple service definitions.
"""

from abc import ABC
from typing import TypeVar, Generic, ClassVar
import re

from sqlmodel import SQLModel, Session, select


T = TypeVar("T", bound=SQLModel)  # Database model
C = TypeVar("C", bound=SQLModel)  # Create schema


def format_handle(name: str) -> str:
    """Convert name to URL-friendly handle."""
    handle = name.lower().strip()
    handle = re.sub(r'[^\w\s-]', '', handle)
    handle = re.sub(r'[\s_]+', '-', handle)
    handle = re.sub(r'-+', '-', handle)
    return handle.strip('-')


class BaseService(ABC, Generic[T, C]):
    """
    Abstract base service class that provides common CRUD operations.
    
    Subclasses must define:
        - model: The SQLModel table class
        - lookup_id_field: Field name for numeric lookups (default: "id")
        - lookup_str_field: Field name for string lookups (default: "label")
        - has_handle: Whether to generate handle from name on create (default: False)
    """
    
    model: ClassVar[type[T]]
    lookup_id_field: ClassVar[str] = "id"
    lookup_str_field: ClassVar[str] = "label"
    has_handle: ClassVar[bool] = False
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all(self) -> list[T]:
        """Get all records."""
        return self.db.exec(select(self.model)).all()
    
    def get(self, value: int | str) -> T | None:
        """Get record by id/code (numeric) or label/name (string)."""
        if isinstance(value, int) or (isinstance(value, str) and value.isdigit()):
            id_field = getattr(self.model, self.lookup_id_field)
            return self.db.exec(
                select(self.model).where(id_field == int(value))
            ).first()
        else:
            str_field = getattr(self.model, self.lookup_str_field)
            return self.db.exec(
                select(self.model).where(str_field.ilike(value))
            ).first()
    
    def create(self, data: C) -> T:
        """Create a new record."""
        if self.has_handle:
            handle = format_handle(data.name)
            db_obj = self.model(**data.model_dump(), handle=handle)
        else:
            db_obj = self.model.model_validate(data)
        
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def delete(self, id: int) -> bool:
        """Delete a record by ID."""
        obj = self.db.exec(
            select(self.model).where(self.model.id == id)
        ).first()
        
        if obj:
            self.db.delete(obj)
            self.db.commit()
            return True
        return False


# =============================================================================
# Simple Service Definitions
# These services have no custom methods, only configuration.
# Imports are at module level since these models have no circular deps.
# =============================================================================

from app.models.db.element import Element
from app.models.db.type import Type
from app.models.db.ability import Ability
from app.models.db.character import Character
from app.models.db.association import Association
from app.models.schemas.element import ElementCreate
from app.models.schemas.type import TypeCreate
from app.models.schemas.ability import AbilityCreate
from app.models.schemas.character import CharacterCreate
from app.models.schemas.association import AssociationCreate


class ElementService(BaseService[Element, ElementCreate]):
    """Service for Element CRUD operations."""
    model = Element
    lookup_id_field = "id"
    lookup_str_field = "label"
    has_handle = False


class TypeService(BaseService[Type, TypeCreate]):
    """Service for Type CRUD operations."""
    model = Type
    lookup_id_field = "id"
    lookup_str_field = "label"
    has_handle = False


class AbilityService(BaseService[Ability, AbilityCreate]):
    """Service for Ability CRUD operations."""
    model = Ability
    lookup_id_field = "code"
    lookup_str_field = "name"
    has_handle = True


class CharacterService(BaseService[Character, CharacterCreate]):
    """Service for Character CRUD operations."""
    model = Character
    lookup_id_field = "id"
    lookup_str_field = "label"
    has_handle = False


class AssociationService(BaseService[Association, AssociationCreate]):
    """Service for Association CRUD operations."""
    model = Association
    lookup_id_field = "code"
    lookup_str_field = "name"
    has_handle = True

