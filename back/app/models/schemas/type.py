from sqlmodel import SQLModel


class TypeCreate(SQLModel):
    """Request body for creating a type."""
    label: str
    icon: str | None = None


class TypeRead(SQLModel):
    """Response model for a type."""
    id: int
    label: str
    icon: str | None = None

