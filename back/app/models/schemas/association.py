from datetime import datetime

from app.models.base.association import AssociationBase


class AssociationCreate(AssociationBase):
    """Request body for creating an association."""
    pass


class AssociationRead(AssociationBase):
    """Response model for an association."""
    id: int
    created_at: datetime
    handle: str
