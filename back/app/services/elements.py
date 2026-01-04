from app.models.db.element import Element
from app.models.schemas.element import ElementCreate
from app.services.base import BaseService


class ElementService(BaseService[Element, ElementCreate]):
    """Service for Element CRUD operations."""
    
    model = Element
    lookup_id_field = "id"
    lookup_str_field = "label"
    has_handle = False
