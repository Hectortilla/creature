from sqlmodel import SQLModel
from datetime import datetime


class AbilityCreate(SQLModel):
    """Request body for creating an ability."""
    code: int
    name: str
    description: str | None = None
    type: str | None = None


class AbilityRead(SQLModel):
    """Response model for an ability."""
    id: int
    created_at: datetime
    code: int
    name: str
    handle: str
    description: str | None = None
    type: str | None = None

