from datetime import datetime

from pydantic import computed_field

from app.models.base.deck import DeckBase
from app.models.game.state import GameConfiguration
from app.models.schemas.card import CardReadWithRelations


class DeckCreate(DeckBase):
    """Schema for creating a deck."""

    pass


class DeckUpdate(DeckBase):
    """Schema for updating a deck."""

    name: str | None = None  # type: ignore[assignment]  # partial-update override of DeckBase.name
    description: str | None = None


class DeckRead(DeckBase):
    """Schema for reading a deck."""

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime


class DeckReadSummary(DeckRead):
    """Lightweight schema for deck listing (without full card data)."""

    card_count: int = 0

    @computed_field
    @property
    def is_valid_for_playing(self) -> bool:
        return self.card_count == GameConfiguration().deck_size


class DeckReadWithCards(DeckRead):
    """Schema for reading a deck with its cards."""

    cards: list[CardReadWithRelations] = []

    @computed_field
    @property
    def is_valid_for_playing(self) -> bool:
        return len(self.cards) == GameConfiguration().deck_size
