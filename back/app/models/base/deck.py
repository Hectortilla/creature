from sqlmodel import Field, SQLModel


class DeckBase(SQLModel):
    """Base deck model with common fields."""

    name: str = Field(max_length=255)
    description: str | None = None

    def __str__(self) -> str:
        return self.name
