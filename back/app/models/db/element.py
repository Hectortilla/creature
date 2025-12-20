from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import Integer


class Element(SQLModel, table=True):
    __tablename__ = "elements"
    
    id: int | None = Field(default=None, primary_key=True)
    label: str = Field(max_length=100, unique=True)
    icon: str | None = Field(default=None, max_length=255)
    color: str | None = Field(default=None, max_length=50)
    strengths: list[int] | None = Field(default=None, sa_column=Column(ARRAY(Integer)))
    weaknesses: list[int] | None = Field(default=None, sa_column=Column(ARRAY(Integer)))

