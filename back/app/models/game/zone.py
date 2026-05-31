"""
Zone State Model

Represents the state of a single zone for a player.
"""

from __future__ import annotations

from typing import Any

from pydantic import computed_field

from app.models.game.base import GameBaseModel
from app.models.game.enums import Zone


class ZoneState(GameBaseModel):
    """
    Represents the state of a single zone for a player.
    """

    zone: Zone
    owner_id: str
    card_ids: list[str] = []
    max_capacity: int | None = None

    @computed_field
    @property
    def is_full(self) -> bool:
        """Check if the zone is at capacity."""
        if self.max_capacity is None:
            return False
        return len(self.card_ids) >= self.max_capacity

    def model_post_init(self, __context: Any) -> None:
        """Set capacity limits based on zone type."""
        if self.max_capacity is None:
            if self.zone == Zone.SUPPORTING:
                object.__setattr__(self, "max_capacity", 3)
            elif self.zone == Zone.ATTACKING:
                object.__setattr__(self, "max_capacity", 2)

    def available_slots(self) -> float:
        """Number of available slots, or ``inf`` for an uncapped zone (DECK/HAND)."""
        if self.max_capacity is None:
            return float("inf")
        return max(0, self.max_capacity - len(self.card_ids))

    def add_card(self, card_id: str) -> bool:
        """Add a card to the zone. Returns False if zone is full."""
        if self.is_full:
            return False
        self.card_ids.append(card_id)
        return True

    def remove_card(self, card_id: str) -> bool:
        """Remove a card from the zone. Returns False if card not found."""
        if card_id in self.card_ids:
            self.card_ids.remove(card_id)
            return True
        return False


__all__ = ["ZoneState"]
