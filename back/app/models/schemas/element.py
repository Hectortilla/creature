from sqlmodel import SQLModel


class ElementCreate(SQLModel):
    """Request body for creating an element."""
    label: str
    icon: str | None = None
    color: str | None = None
    strengths: list[int] | None = None
    weaknesses: list[int] | None = None


class ElementRead(SQLModel):
    """Response model for an element."""
    id: int
    label: str
    icon: str | None = None
    color: str | None = None
    strengths: list[int] | None = None
    weaknesses: list[int] | None = None

