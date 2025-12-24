from sqlmodel import SQLModel, Field


class CharacterBase(SQLModel):
    label: str = Field(max_length=100)
    icon: str | None = Field(default=None, max_length=255)

