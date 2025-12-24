from sqlmodel import SQLModel, Field


class TypeBase(SQLModel):
    """Base model with shared fields for Type."""
    label: str = Field(max_length=100)
    icon: str | None = Field(default=None, max_length=255)

