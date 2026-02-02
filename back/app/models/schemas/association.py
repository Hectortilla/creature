from datetime import datetime

from app.models.base.association import AssociationBase


class AssociationCreate(AssociationBase):
    pass


class AssociationRead(AssociationBase):
    id: int
    created_at: datetime
    handle: str
