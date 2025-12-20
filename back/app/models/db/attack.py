from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from app.models.db.element import Element


class Attack(SQLModel, table=True):
    __tablename__ = "attacks"
    
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    code: int = Field(unique=True)
    name: str = Field(max_length=255)
    handle: str = Field(default="", max_length=255)
    description: str | None = Field(default=None)
    damage: int | None = Field(default=None)
    type: str | None = Field(default=None, max_length=50)
    dice_rolls: int | None = Field(default=None)
    necessary_force: dict | None = Field(default=None, sa_column=Column(JSONB))
    effect: str | None = Field(default=None)
    element_id: int | None = Field(default=None, foreign_key="elements.id")
    
    # Relationship
    element: Optional["Element"] = Relationship()

