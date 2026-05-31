from datetime import datetime

from sqlmodel import Field

from app.models.base.association import AssociationBase
from app.utils.time import utcnow


class Association(AssociationBase, table=True):
    __tablename__ = "associations"

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utcnow)
    code: int = Field(unique=True)
    handle: str = Field(default="", max_length=255)
