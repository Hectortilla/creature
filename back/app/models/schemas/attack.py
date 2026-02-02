from datetime import datetime

from app.models.base.attack import AttackBase
from app.models.schemas.element import ElementRead


class AttackCreate(AttackBase):
    element_id: int | None = None


class AttackRead(AttackBase):
    id: int
    created_at: datetime
    handle: str
    element_id: int | None = None


class AttackReadWithElement(AttackRead):
    element: ElementRead | None = None
    strengths: list[int] | None = None
    weaknesses: list[int] | None = None
