from app.models.db import Character
from app.models.schemas import CharacterCreate
from app.services.base import BaseService


class CharacterService(BaseService[Character, CharacterCreate]):
    """Service for Character CRUD operations."""
    
    model = Character
    lookup_id_field = "id"
    lookup_str_field = "label"
    has_handle = False
