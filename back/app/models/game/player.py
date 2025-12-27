"""
Player State Model

Represents a player's state in the game.
"""

from __future__ import annotations

from typing import Any

from pydantic import Field

from app.models.game.base import GameBaseModel
from app.models.game.enums import Zone
from app.models.game.element import ElementPool
from app.models.game.zone import ZoneState


class PlayerState(GameBaseModel):
    """
    Represents a player's state in the game.
    """
    player_id: str
    name: str
    turn_count: int = 0
    element_pool: ElementPool = Field(default_factory=ElementPool)
    zones: dict[str, ZoneState] = {}  # Zone name -> ZoneState
    has_passed_phase: bool = False
    
    def model_post_init(self, __context: Any) -> None:
        """Initialize zones if not provided."""
        if not self.zones:
            self.zones = {
                zone.name: ZoneState(zone=zone, owner_id=self.player_id)
                for zone in Zone
            }
    
    def get_zone(self, zone: Zone) -> ZoneState:
        """Get a specific zone."""
        return self.zones[zone.name]
    
    def get_active_cards(self) -> list[str]:
        """Get all card IDs in active zones (supporting + attacking)."""
        return (
            self.zones[Zone.SUPPORTING.name].card_ids +
            self.zones[Zone.ATTACKING.name].card_ids
        )
    
    def has_defenders(self) -> bool:
        """Check if the player has any cards that can defend."""
        return bool(self.get_active_cards())
    
    def reset_turn_state(self) -> None:
        """Reset per-turn state at the start of a new turn."""
        self.has_passed_phase = False


__all__ = ["PlayerState"]

