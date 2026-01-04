from app.models.db.type import Type
from app.models.schemas.type import TypeCreate
from app.services.base import BaseService


class TypeService(BaseService[Type, TypeCreate]):
    """Service for Type CRUD operations."""
    
    model = Type
    lookup_id_field = "id"
    lookup_str_field = "label"
    has_handle = False
