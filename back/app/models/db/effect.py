from datetime import datetime
from typing import Any

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

from app.utils.time import utcnow


class Effect(SQLModel, table=True):
    """Data-driven effect atom attached to an ability, attack, or association."""

    __tablename__ = "effects"

    id: int | None = Field(default=None, primary_key=True)
    owner_kind: str = Field(index=True, max_length=32)
    owner_id: int = Field(index=True)
    atom_type: str = Field(index=True, max_length=128)
    trigger: str | None = Field(default=None, max_length=64)
    params: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSONB, nullable=False))
    sort_order: int = 0
    script_id: str | None = Field(default=None, max_length=128)
    enabled: bool = True
    notes: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
