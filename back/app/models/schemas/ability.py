from datetime import datetime

from app.models.base.ability import AbilityBase


class AbilityCreate(AbilityBase):
    """Request body for creating an ability."""
    pass


class AbilityRead(AbilityBase):
    """Response model for an ability."""
    id: int
    created_at: datetime
    handle: str
