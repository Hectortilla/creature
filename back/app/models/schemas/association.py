from sqlmodel import SQLModel
from datetime import datetime


class AssociationCreate(SQLModel):
    """Request body for creating an association."""
    code: int
    name: str
    description: str | None = None


class AssociationRead(SQLModel):
    """Response model for an association."""
    id: int
    created_at: datetime
    code: int
    name: str
    handle: str
    description: str | None = None

