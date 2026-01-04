from app.models.db.association import Association
from app.models.schemas.association import AssociationCreate
from app.services.base import BaseService


class AssociationService(BaseService[Association, AssociationCreate]):
    """Service for Association CRUD operations."""
    
    model = Association
    lookup_id_field = "code"
    lookup_str_field = "name"
    has_handle = True
