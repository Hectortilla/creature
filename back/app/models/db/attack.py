from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, Field, Relationship

from app.models.base.attack import AttackBase
from app.utils.time import utcnow

if TYPE_CHECKING:
    from app.models.db.element import Element


class Attack(AttackBase, table=True):
    __tablename__ = "attacks"

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utcnow)
    code: int = Field(unique=True)
    handle: str = Field(default="", max_length=255)
    necessary_force: list[dict] | None = Field(default=None, sa_column=Column(JSONB))
    dice_rolls: int | None = None
    element_id: int | None = Field(default=None, foreign_key="elements.id")

    # Relationship
    element: Optional["Element"] = Relationship()
