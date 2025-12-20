from sqlmodel import SQLModel


class CharacterCreate(SQLModel):
    """Request body for creating a character."""
    label: str
    icon: str | None = None


class CharacterRead(SQLModel):
    """Response model for a character."""
    id: int
    label: str
    icon: str | None = None

