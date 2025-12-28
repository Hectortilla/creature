"""
Game Card Model

Represents a card instance during gameplay with runtime state.
"""

from __future__ import annotations

import uuid
from typing import Optional, Any

from pydantic import field_serializer, computed_field, model_validator

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


class GameCardInput(GameBaseModel):
    """
    Input format for card data when creating a game.
    
    This is the format expected by the game engine's create_game method.
    Represents card data as it comes from the deck before being instantiated.
    """
    id: int
    name: str
    health: int = 10
    physical_defence: int = 0
    magic_defence: int = 0
    element_ids: list[int] = []
    element_contribution: list[dict[str, int]] = []
    attacks: list[dict[str, Any]] = []
    skill_ids: list[int] = []
    association_ids: list[int] = []
    is_evolution: bool = False
    evolves_from_id: Optional[int] = None
    
    @classmethod
    def from_card_read(cls, card: Any) -> "GameCardInput":
        """
        Create GameCardInput from CardReadWithRelations.
        
        Args:
            card: CardReadWithRelations instance from deck enrichment
            
        Returns:
            GameCardInput instance ready for game engine
        """
        # Build element_ids list
        element_ids = []
        if card.first_element_id:
            element_ids.append(card.first_element_id)
        if card.second_element_id:
            element_ids.append(card.second_element_id)
        
        # Build element_contribution (default: 1 of each element)
        element_contribution = []
        if card.first_element_id:
            element_contribution.append({"element_id": card.first_element_id, "amount": 1})
        if card.second_element_id:
            element_contribution.append({"element_id": card.second_element_id, "amount": 1})
        
        # Build attacks list
        attacks = []
        if card.first_attack:
            attacks.append({
                "id": card.first_attack.id,
                "name": card.first_attack.name,
                "damage": card.first_attack.damage or 0,
                "type": card.first_attack.type or "physical",
                "element_id": card.first_attack.element_id or 0,
                "necessary_force": card.first_attack.necessary_force or [],
                "effect": card.first_attack.effect,
                "description": card.first_attack.description,
                "dice_rolls": card.first_attack.dice_rolls,
            })
        if card.second_attack:
            attacks.append({
                "id": card.second_attack.id,
                "name": card.second_attack.name,
                "damage": card.second_attack.damage or 0,
                "type": card.second_attack.type or "physical",
                "element_id": card.second_attack.element_id or 0,
                "necessary_force": card.second_attack.necessary_force or [],
                "effect": card.second_attack.effect,
                "description": card.second_attack.description,
                "dice_rolls": card.second_attack.dice_rolls,
            })
        
        # Build skill_ids and association_ids
        skill_ids = []
        if card.ability_id:
            skill_ids.append(card.ability_id)
        
        association_ids = []
        if card.association_id:
            association_ids.append(card.association_id)
        
        return cls(
            id=card.id,
            name=card.name,
            health=card.health or 10,
            physical_defence=card.physical_defence or 0,
            magic_defence=card.magic_defence or 0,
            element_ids=element_ids,
            element_contribution=element_contribution,
            attacks=attacks,
            skill_ids=skill_ids,
            association_ids=association_ids,
            is_evolution=card.is_evolution_id is not None,
            evolves_from_id=card.is_evolution_id,
        )


__all__ = ["GameCard", "GameCardInput"]

