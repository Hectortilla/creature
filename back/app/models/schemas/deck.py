from datetime import datetime
from typing import Optional

from app.models.base.deck import DeckBase
from app.models.schemas.card import CardRead


class DeckCreate(DeckBase):
    """Schema for creating a deck."""
    pass


class DeckUpdate(DeckBase):
    """Schema for updating a deck."""
    name: Optional[str] = None
    description: Optional[str] = None


class DeckRead(DeckBase):
    """Schema for reading a deck."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime


class DeckReadWithCards(DeckRead):
    """Schema for reading a deck with its cards."""
    cards: list[CardRead] = []

