"""
Game Card Model

Represents a card instance during gameplay with runtime state.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional, Any

from pydantic import Field, computed_field, model_validator

from app.models.core.card import CardIdentityFields, CardCombatFields
from app.models.game.base import GameBaseModel
from app.models.game.enums import Zone, CardStatus, StatusType
from app.models.game.element import ElementContribution
from app.models.game.attack import AttackDefinition

if TYPE_CHECKING:
    from app.models.schemas.attack import AttackReadWithElement
    from app.models.schemas.card import CardReadWithRelations


class EffectSpec(GameBaseModel):
    """Serializable effect atom data copied from the catalog into runtime setup."""

    id: int
    owner_kind: str
    owner_id: int
    atom_type: str
    trigger: Optional[str] = None
    params: dict[str, Any] = Field(default_factory=dict)
    sort_order: int = 0
    script_id: Optional[str] = None


class ActiveStatus(GameBaseModel):
    """Runtime status applied by an effect atom."""

    status_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status_type: StatusType
    source_card_id: str = ""
    source_atom_id: Optional[int] = None
    remaining_turns: int = 1
    tick_on: str = "none"
    expires_on: str = "own_turn_end"
    payload: dict[str, Any] = Field(default_factory=dict)


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
    type_id: Optional[int] = None
    character_id: Optional[int] = None
    character_name: Optional[str] = None
    
    # Abilities
    attacks: list[AttackDefinition] = []
    ability_ids: list[int] = []
    association_ids: list[int] = []
    
    # Evolution
    evolves_from_id: Optional[int] = None
    
    # Runtime state
    zone: Zone = Zone.DECK
    status: CardStatus = CardStatus.READY
    turns_in_zone: int = 0
    associations: list[str] = []  # instance_ids
    association_target_id: Optional[str] = None
    active_statuses: list[ActiveStatus] = Field(default_factory=list)
    effect_specs: list[EffectSpec] = Field(default_factory=list, exclude=True)
    effect_atoms: list[Any] = Field(default_factory=list, exclude=True)
    attack_last_used: dict[int, int] = Field(default_factory=dict)
    has_attacked_this_turn: bool = False
    swapped_this_turn: bool = False
    
    # Computed fields - included in model_dump() automatically
    @computed_field
    @property
    def is_alive(self) -> bool:
        """Check if the card is still alive."""
        return self.current_health > 0
    
    @computed_field
    @property
    def can_attack(self) -> bool:
        """Check if the card can attack.

        Note: Swapped cards CAN attack if they can afford it with other cards'
        elements. This matches the rule: "The attacking card may still attack."
        Element affordability naturally limits this since swapped cards don't
        contribute elements on the turn they're swapped.
        """
        return (
            self.zone == Zone.ATTACKING
            and not self.has_attacked_this_turn
            and self.status != CardStatus.ASSOCIATED
            and not any(status.status_type == StatusType.BLOCK_ATTACK for status in self.active_statuses)
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


class AttackInput(GameBaseModel):
    """
    Input format for a single attack when creating a game.

    Mirrors the dict shape produced by enrichment/serialization; `type` stays
    a string at this boundary and is mapped to DamageType when the attack is
    materialized into an AttackDefinition in _create_game_card.
    """
    id: int
    name: str
    damage: int = 0
    type: str = "physical"
    element_id: int = 0
    necessary_force: list[ElementContribution] = []
    effect: Optional[str] = None
    description: Optional[str] = None
    dice_rolls: Optional[int] = None


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
    element_contribution: list[ElementContribution] = []
    type_id: Optional[int] = None
    character_id: Optional[int] = None
    character_name: Optional[str] = None
    attacks: list[AttackInput] = []
    ability_ids: list[int] = []
    association_ids: list[int] = []
    effect_specs: list[EffectSpec] = Field(default_factory=list)
    evolves_from_id: Optional[int] = None
    
    @classmethod
    def _normalize_necessary_force(cls, necessary_force: list[dict[str, Any]] | None) -> list[dict]:
        """
        Normalize necessary_force structure: convert from {value, elementData} to {element_id, amount}.
        
        Handles both formats:
        - Frontend format: {value: X, elementData: {id: Y}}
        - Already normalized: {element_id: X, amount: Y}
        """
        if not necessary_force:
            return []
        
        normalized = []
        for force in necessary_force:
            if isinstance(force, dict):
                # Handle both formats: {value, elementData} or {element_id, amount}
                if "elementData" in force and "value" in force:
                    # Convert from frontend format: {value: X, elementData: {id: Y}}
                    normalized.append({
                        "element_id": force["elementData"]["id"],
                        "amount": force["value"]
                    })
                elif "element_id" in force and "amount" in force:
                    # Already in correct format
                    normalized.append(force)
        
        return normalized
    
    @classmethod
    def _build_attack_input(cls, attack: AttackReadWithElement) -> AttackInput:
        """Build AttackInput from an enriched attack object."""
        return AttackInput(
            id=attack.id,
            name=attack.name,
            damage=attack.damage or 0,
            type=attack.type or "physical",
            element_id=attack.element_id or 0,
            necessary_force=cls._normalize_necessary_force(attack.necessary_force),
            effect=attack.effect,
            description=attack.description,
            dice_rolls=attack.dice_rolls,
        )
    
    @classmethod
    def from_card_read(cls, card: CardReadWithRelations) -> "GameCardInput":
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
            attacks.append(cls._build_attack_input(card.first_attack))
        if card.second_attack:
            attacks.append(cls._build_attack_input(card.second_attack))
        
        # Build ability_ids and association_ids
        ability_ids = []
        if card.ability_id:
            ability_ids.append(card.ability_id)
        
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
            type_id=card.type_id,
            character_id=card.character_id,
            character_name=card.character.label if card.character else None,
            attacks=attacks,
            ability_ids=ability_ids,
            association_ids=association_ids,
            effect_specs=[
                EffectSpec.model_validate(effect.model_dump())
                for effect in getattr(card, "effects", [])
            ],
            evolves_from_id=card.is_evolution_id,
        )


__all__ = ["GameCard", "GameCardInput", "AttackInput", "EffectSpec", "ActiveStatus"]
