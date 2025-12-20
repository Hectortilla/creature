from sqlmodel import SQLModel
from datetime import datetime

from app.models.schemas.element import ElementRead


class AttackCreate(SQLModel):
    """Request body for creating an attack."""
    code: int
    name: str
    description: str | None = None
    damage: int | None = None
    type: str | None = None
    element_id: int | None = None
    dice_rolls: int | None = None
    necessary_force: dict | None = None
    effect: str | None = None


class AttackRead(SQLModel):
    """Response model for an attack."""
    id: int
    created_at: datetime
    code: int
    name: str
    handle: str
    description: str | None = None
    damage: int | None = None
    type: str | None = None
    element_id: int | None = None
    dice_rolls: int | None = None
    necessary_force: dict | None = None
    effect: str | None = None


class AttackReadWithElement(AttackRead):
    """Response model for an attack with element details."""
    element: ElementRead | None = None
    strengths: list[int] | None = None
    weaknesses: list[int] | None = None

