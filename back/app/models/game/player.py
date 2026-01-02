"""
Player State Model

Represents a player's state in the game.
"""

from __future__ import annotations

import random
from typing import Any, Optional

from pydantic import Field, model_validator

from app.models.game.base import GameBaseModel
from app.models.game.enums import Zone
from app.models.game.element import ElementPool
from app.models.game.zone import ZoneState


class ZoneDict(dict):
    """Dict wrapper that supports both Zone enum and string keys."""
    def __getitem__(self, key: Zone | str) -> ZoneState:
        if isinstance(key, Zone):
            return super().__getitem__(key.name)
        return super().__getitem__(key)
    
    def __contains__(self, key: Zone | str) -> bool:
        if isinstance(key, Zone):
            return super().__contains__(key.name)
        return super().__contains__(key)


class PlayerState(GameBaseModel):
    """
    Represents a player's state in the game.
    """
    player_id: str
    name: str
    turn_count: int = 0
    element_pool: ElementPool = Field(default_factory=ElementPool)
    zones: dict[str, ZoneState] = Field(default_factory=dict)  # Zone name -> ZoneState
    has_passed_phase: bool = False
    deck: Optional[list[dict]] = None  # Serialized deck data
    
    @model_validator(mode='after')
    def initialize_zones(self) -> "PlayerState":
        """Initialize zones if not provided or empty."""
        # Always ensure all zones are initialized
        if not self.zones or len(self.zones) == 0:
            object.__setattr__(self, 'zones', {
                zone.name: ZoneState(zone=zone, owner_id=self.player_id)
                for zone in Zone
            })
        # Ensure all zones exist (in case some are missing)
        for zone in Zone:
            if zone.name not in self.zones:
                self.zones[zone.name] = ZoneState(zone=zone, owner_id=self.player_id)
        # Wrap zones dict with ZoneDict for enum access
        object.__setattr__(self, 'zones', ZoneDict(self.zones))
        return self
    
    def get_zone(self, zone: Zone) -> ZoneState:
        """Get a specific zone."""
        return self.zones[zone]
    
    def get_active_cards(self) -> list[str]:
        """Get all card IDs in active zones (supporting + attacking)."""
        return (
            self.zones[Zone.SUPPORTING].card_ids +
            self.zones[Zone.ATTACKING].card_ids
        )
    
    def has_defenders(self) -> bool:
        """Check if the player has any cards that can defend."""
        return bool(self.get_active_cards())
    
    def reset_turn_state(self) -> None:
        """Reset per-turn state at the start of a new turn."""
        self.has_passed_phase = False
    
    def shuffle_deck(self) -> None:
        """Shuffle the player's deck."""
        random.shuffle(self.zones[Zone.DECK].card_ids)


__all__ = ["PlayerState"]

