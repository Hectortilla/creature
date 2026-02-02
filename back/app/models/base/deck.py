from sqlmodel import SQLModel, Field


class DeckBase(SQLModel):
    """Base deck model with common fields."""
    name: str = Field(max_length=255)
    description: str | None = None

