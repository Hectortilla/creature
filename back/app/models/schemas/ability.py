from datetime import datetime

from app.models.base.ability import AbilityBase


class AbilityCreate(AbilityBase):
    pass


class AbilityRead(AbilityBase):
    id: int
    created_at: datetime
    handle: str
