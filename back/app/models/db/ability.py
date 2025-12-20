from sqlmodel import SQLModel, Field
from datetime import datetime


class Ability(SQLModel, table=True):
    __tablename__ = "abilities"
    
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    code: int = Field(unique=True)
    name: str = Field(max_length=255)
    handle: str = Field(default="", max_length=255)
    description: str | None = Field(default=None)
    type: str | None = Field(default=None, max_length=50)

