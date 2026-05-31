from sqlalchemy import Integer
from sqlalchemy.dialects.postgresql import ARRAY
from sqlmodel import Column, Field

from app.models.base.element import ElementBase


class Element(ElementBase, table=True):
    __tablename__ = "elements"

    id: int | None = Field(default=None, primary_key=True)
    label: str = Field(max_length=100, unique=True)
    strengths: list[int] | None = Field(default=None, sa_column=Column(ARRAY(Integer)))
    weaknesses: list[int] | None = Field(default=None, sa_column=Column(ARRAY(Integer)))
