from sqlmodel import Field

from app.models.base.character import CharacterBase


class Character(CharacterBase, table=True):
    __tablename__ = "characters"

    id: int | None = Field(default=None, primary_key=True)
    label: str = Field(max_length=100, unique=True)
