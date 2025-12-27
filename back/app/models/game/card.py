"""
Game Card Model

Represents a card instance during gameplay with runtime state.
"""

from __future__ import annotations

import uuid
from typing import Optional

from pydantic import field_serializer, computed_field

from app.models.core.card import CardIdentityFields, CardCombatFields
from app.models.game.base import GameBaseModel
from app.models.game.enums import Zone, CardStatus
from app.models.game.element import ElementContribution
from app.models.game.attack import AttackDefinition


class GameCard(CardIdentityFields, CardCombatFields, GameBaseModel):
    """
    Represents a card instance in the game.
    
    This is distinct from the database Card model - this represents
    a specific instance of a card during gameplay with runtime state.
    
    Inherits shared fields from:
    - CardIdentityFields: name, description
    - CardCombatFields: health, physical_defence, magic_defence
    
    Adds game-specific fields for runtime state.
    """
    instance_id: str
    card_id: int
    owner_id: str
    
    # Override combat stats to be required (not Optional) for game runtime
    health: int  # max health
    physical_defence: int
    magic_defence: int
    
    # Runtime mutable health (separate from max health)
    current_health: int
    
    # Elements
    element_ids: list[int] = []
    element_contribution: list[ElementContribution] = []
    
    # Abilities
    attacks: list[AttackDefinition] = []
    skill_ids: list[int] = []
    association_ids: list[int] = []
    
    # Evolution
    is_evolution: bool = False
    evolves_from_id: Optional[int] = None
    
    # Runtime state
    zone: Zone = Zone.DECK
    status: CardStatus = CardStatus.READY
    turns_in_zone: int = 0
    associations: list[str] = []  # instance_ids
    has_attacked_this_turn: bool = False
    swapped_this_turn: bool = False
    
    @field_serializer('zone')
    def serialize_zone(self, value: Zone) -> str:
        return value.name
    
    @field_serializer('status')
    def serialize_status(self, value: CardStatus) -> str:
        return value.name
    
    # Computed fields - included in model_dump() automatically
    @computed_field
    @property
    def is_alive(self) -> bool:
        """Check if the card is still alive."""
        return self.current_health > 0
    
    @computed_field
    @property
    def can_attack(self) -> bool:
        """Check if the card can attack."""
        return (
            self.zone == Zone.ATTACKING
            and not self.has_attacked_this_turn
            and self.status != CardStatus.ASSOCIATED
        )
    
    @computed_field
    @property
    def can_promote(self) -> bool:
        """Check if the card can be promoted to attacking zone."""
        return (
            self.zone == Zone.SUPPORTING
            and self.turns_in_zone >= 1
            and self.status != CardStatus.ASSOCIATED
        )
    
    @computed_field
    @property
    def can_evolve(self) -> bool:
        """Check if the card can be evolved."""
        return (
            self.zone in (Zone.SUPPORTING, Zone.ATTACKING)
            and self.turns_in_zone >= 1
            and self.status != CardStatus.ASSOCIATED
        )
    
    @classmethod
    def create(cls, card_id: int, owner_id: str, name: str,
               health: int, physical_defence: int, magic_defence: int,
               **kwargs) -> "GameCard":
        """Factory method to create a new game card instance."""
        return cls(
            instance_id=str(uuid.uuid4()),
            card_id=card_id,
            owner_id=owner_id,
            name=name,
            health=health,
            current_health=health,
            physical_defence=physical_defence,
            magic_defence=magic_defence,
            **kwargs
        )
    
    def get_element_contribution(self) -> list[ElementContribution]:
        """Get element contribution, considering status."""
        if self.swapped_this_turn or self.status == CardStatus.ASSOCIATED:
            return []
        return self.element_contribution
    
    def apply_damage(self, amount: int) -> int:
        """Apply damage to the card. Returns the actual damage dealt."""
        actual_damage = max(0, amount)
        self.current_health -= actual_damage
        return actual_damage
    
    def heal(self, amount: int) -> int:
        """Heal the card. Returns the actual healing done."""
        old_health = self.current_health
        self.current_health = min(self.health, self.current_health + amount)
        return self.current_health - old_health
    
    def reset_turn_flags(self) -> None:
        """Reset per-turn flags at the start of a new turn."""
        self.has_attacked_this_turn = False
        self.swapped_this_turn = False
        if self.status == CardStatus.SWAPPED:
            self.status = CardStatus.READY
    
    def increment_zone_turns(self) -> None:
        """Increment the turns spent in the current zone."""
        self.turns_in_zone += 1


__all__ = ["GameCard"]

