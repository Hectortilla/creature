from datetime import datetime

from sqlmodel import Field

from app.models.base.ability import AbilityBase
from app.utils.time import utcnow


class Ability(AbilityBase, table=True):
    __tablename__ = "abilities"

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utcnow)
    code: int = Field(unique=True)
    handle: str = Field(default="", max_length=255)
