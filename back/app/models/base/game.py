"""
Base models for game runtime state.

These models define the core structures used during gameplay,
using Pydantic BaseModel for validation and serialization.
"""

from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, ConfigDict


class GameBaseModel(BaseModel):
    """
    Base class for all game models.
    
    Provides consistent configuration and serialization behavior.
    Uses Pydantic v2 with:
    - model_dump() for dict serialization
    - model_dump_json() for JSON string
    - model_validate() for creating from dict
    """
    model_config = ConfigDict(
        # Allow population by field name or alias
        populate_by_name=True,
        # Validate on assignment
        validate_assignment=True,
        # Allow arbitrary types (for enums, etc.)
        arbitrary_types_allowed=True,
        # Use enum values in serialization
        use_enum_values=False,
    )
    
    def to_dict(self) -> dict[str, Any]:
        """
        Serialize to dictionary.
        
        Convenience wrapper around model_dump() that:
        - Converts enums to their names
        - Handles nested models
        """
        return self.model_dump(mode='python')
    
    def to_json_dict(self) -> dict[str, Any]:
        """
        Serialize to JSON-compatible dictionary.
        
        Uses mode='json' which converts all types to JSON-safe values.
        """
        return self.model_dump(mode='json')


class ElementContributionBase(GameBaseModel):
    """
    Represents element contribution from a card.
    
    This is the base model used for element costs, contributions,
    and any element+amount pair in the game.
    """
    element_id: int
    amount: int


class AttackCostBase(GameBaseModel):
    """
    Represents the cost to perform an attack.
    """
    costs: list[ElementContributionBase] = []
    
    def can_afford(self, available_elements: dict[int, int]) -> bool:
        """Check if the cost can be paid with available elements."""
        for cost in self.costs:
            if available_elements.get(cost.element_id, 0) < cost.amount:
                return False
        return True


class GameCardStats(GameBaseModel):
    """
    Combat statistics for a game card.
    """
    max_health: int
    current_health: int
    physical_defense: int
    magical_defense: int
    
    def is_alive(self) -> bool:
        """Check if the card is still alive."""
        return self.current_health > 0


class GameConfigurationBase(GameBaseModel):
    """
    Base configuration options for a game.
    """
    deck_size: int = 22
    initial_draw: int = 4
    normal_draw: int = 1
    supporting_zone_size: int = 3
    attacking_zone_size: int = 2
