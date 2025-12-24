from sqlmodel import SQLModel, Field


class AssociationBase(SQLModel):
    """Base model with shared fields for Association."""
    code: int
    name: str = Field(max_length=255)
    description: str | None = None

