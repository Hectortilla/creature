from sqlmodel import SQLModel, Field


class AssociationBase(SQLModel):
    code: int
    name: str = Field(max_length=255)
    description: str | None = None

