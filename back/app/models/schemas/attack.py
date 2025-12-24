from datetime import datetime

from app.models.base.attack import AttackBase
from app.models.schemas.element import ElementRead


class AttackCreate(AttackBase):
    """Request body for creating an attack."""
    element_id: int | None = None


class AttackRead(AttackBase):
    """Response model for an attack."""
    id: int
    created_at: datetime
    handle: str
    element_id: int | None = None


class AttackReadWithElement(AttackRead):
    """Response model for an attack with element details."""
    element: ElementRead | None = None
    strengths: list[int] | None = None
    weaknesses: list[int] | None = None
