from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EffectRead(BaseModel):
    # Read from ORM (SQLModel) Effect rows, not just dicts.
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_kind: str
    owner_id: int
    atom_type: str
    trigger: str | None = None
    params: dict[str, Any] = Field(default_factory=dict)
    sort_order: int = 0
    script_id: str | None = None
    enabled: bool = True
    notes: str | None = None
    created_at: datetime | None = None
