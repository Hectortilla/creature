from sqlmodel import SQLModel, Field


class AbilityBase(SQLModel):
    """Base model with shared fields for Ability."""
    code: int
    name: str = Field(max_length=255)
    description: str | None = None
    type: str | None = Field(default=None, max_length=50)

