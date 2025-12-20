from app.models.db import Ability
from app.models.schemas import AbilityCreate
from app.services.base import BaseService


class AbilityService(BaseService[Ability, AbilityCreate]):
    """Service for Ability CRUD operations."""
    
    model = Ability
    lookup_id_field = "code"
    lookup_str_field = "name"
    has_handle = True
