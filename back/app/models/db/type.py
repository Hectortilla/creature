from sqlmodel import Field

from app.models.base.type import TypeBase


class Type(TypeBase, table=True):
    __tablename__ = "types"

    id: int | None = Field(default=None, primary_key=True)
    label: str = Field(max_length=100, unique=True)
