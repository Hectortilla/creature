"""
Game Events

Defines all events that can occur during a game.
Events are used for event-driven processing and effect triggers.

All events use Pydantic BaseModel for validation and serialization.
"""

from __future__ import annotations

from typing import Any, Optional
from datetime import datetime
from abc import ABC
from pydantic import Field, field_serializer, computed_field

from app.game.enums import Zone, TurnPhase, DamageType
from app.models.base.game import GameBaseModel


class GameEvent(GameBaseModel, ABC):
    """
    Base class for all game events.
    
    Uses Pydantic's model_dump() for serialization.
    event_type is a computed field so it's included automatically.
    """
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    game_id: Optional[str] = None
    
    @computed_field
    @property
    def event_type(self) -> str:
        """Return the type name of this event."""
        return self.__class__.__name__
    
    @field_serializer('timestamp')
    def serialize_timestamp(self, value: datetime) -> str:
        return value.isoformat()


# ============================================================================
# Card Movement Events
# ============================================================================

class CardDrawnEvent(GameEvent):
    """Event fired when a card is drawn from deck to hand."""
    player_id: str = ""
    card_id: str = ""
    cards_remaining: int = 0


class CardMovedEvent(GameEvent):
    """Event fired when a card moves between zones."""
    card_id: str = ""
    owner_id: str = ""
    from_zone: Optional[Zone] = None
    to_zone: Optional[Zone] = None
    
    @field_serializer('from_zone')
    def serialize_from_zone(self, value: Optional[Zone]) -> Optional[str]:
        return value.name if value else None
    
    @field_serializer('to_zone')
    def serialize_to_zone(self, value: Optional[Zone]) -> Optional[str]:
        return value.name if value else None


class CardPlayedEvent(GameEvent):
    """Event fired when a card is played from hand to supporting zone."""
    player_id: str = ""
    card_id: str = ""
    card_name: str = ""


class CardPromotedEvent(GameEvent):
    """Event fired when a card is promoted from supporting to attacking zone."""
    player_id: str = ""
    card_id: str = ""
    card_name: str = ""


class CardSwappedEvent(GameEvent):
    """Event fired when two cards are swapped between zones."""
    player_id: str = ""
    supporting_card_id: str = ""
    attacking_card_id: str = ""


# ============================================================================
# Association & Evolution Events
# ============================================================================

class CardAssociatedEvent(GameEvent):
    """Event fired when a card is associated with another card."""
    player_id: str = ""
    association_card_id: str = ""
    target_card_id: str = ""
    source_zone: Optional[Zone] = None
    
    @field_serializer('source_zone')
    def serialize_source_zone(self, value: Optional[Zone]) -> Optional[str]:
        return value.name if value else None


class CardEvolvedEvent(GameEvent):
    """Event fired when a card evolves."""
    player_id: str = ""
    base_card_id: str = ""
    evolution_card_id: str = ""
    base_card_name: str = ""
    evolution_card_name: str = ""


# ============================================================================
# Combat Events
# ============================================================================

class AttackDeclaredEvent(GameEvent):
    """Event fired when an attack is declared."""
    attacker_owner_id: str = ""
    attacker_id: str = ""
    target_id: str = ""
    attack_id: int = 0
    attack_name: str = ""


class DamageDealtEvent(GameEvent):
    """Event fired when damage is dealt to a card."""
    source_id: str = ""
    target_id: str = ""
    damage_type: Optional[DamageType] = None
    base_damage: int = 0
    element_bonus: int = 0
    defense_reduction: int = 0
    final_damage: int = 0
    remaining_health: int = 0
    
    @field_serializer('damage_type')
    def serialize_damage_type(self, value: Optional[DamageType]) -> Optional[str]:
        return value.name if value else None


class CardDestroyedEvent(GameEvent):
    """Event fired when a card is destroyed (health <= 0)."""
    card_id: str = ""
    owner_id: str = ""
    card_name: str = ""
    destroyed_by: Optional[str] = None


# ============================================================================
# Element Events
# ============================================================================

class ElementsConsumedEvent(GameEvent):
    """Event fired when elements are consumed for an attack."""
    player_id: str = ""
    elements: dict[int, int] = {}
    for_attack_id: int = 0


class ElementsRestoredEvent(GameEvent):
    """Event fired when elements are restored at turn start."""
    player_id: str = ""
    elements: dict[int, int] = {}


# ============================================================================
# Turn & Phase Events
# ============================================================================

class TurnStartedEvent(GameEvent):
    """Event fired at the start of a player's turn."""
    player_id: str = ""
    turn_number: int = 0
    is_first_turn: bool = False


class TurnEndedEvent(GameEvent):
    """Event fired at the end of a player's turn."""
    player_id: str = ""
    turn_number: int = 0


class PhaseChangedEvent(GameEvent):
    """Event fired when the turn phase changes."""
    player_id: str = ""
    from_phase: Optional[TurnPhase] = None
    to_phase: Optional[TurnPhase] = None
    
    @field_serializer('from_phase')
    def serialize_from_phase(self, value: Optional[TurnPhase]) -> Optional[str]:
        return value.name if value else None
    
    @field_serializer('to_phase')
    def serialize_to_phase(self, value: Optional[TurnPhase]) -> Optional[str]:
        return value.name if value else None


# ============================================================================
# Game-Level Events
# ============================================================================

class GameStartedEvent(GameEvent):
    """Event fired when a game starts."""
    player_ids: list[str] = []
    first_player_id: str = ""


class GameEndedEvent(GameEvent):
    """Event fired when the game ends."""
    winner_id: str = ""
    loser_id: str = ""
    reason: str = ""


class NoDefenderEvent(GameEvent):
    """
    Event fired when a player has no defending creatures and is attacked.
    Triggers the forced defend mechanic.
    """
    defender_id: str = ""
    attacker_id: str = ""
    must_defend: bool = False
    game_lost: bool = False


# ============================================================================
# Effect Events
# ============================================================================

class EffectTriggeredEvent(GameEvent):
    """Event fired when an effect is triggered."""
    source_card_id: str = ""
    effect_id: str = ""
    effect_name: str = ""
    trigger_reason: str = ""


class EffectAppliedEvent(GameEvent):
    """Event fired when an effect's result is applied."""
    effect_id: str = ""
    affected_card_ids: list[str] = []
    description: str = ""


# Event type registry for deserialization
EVENT_TYPES = {
    "CardDrawnEvent": CardDrawnEvent,
    "CardMovedEvent": CardMovedEvent,
    "CardPlayedEvent": CardPlayedEvent,
    "CardPromotedEvent": CardPromotedEvent,
    "CardSwappedEvent": CardSwappedEvent,
    "CardAssociatedEvent": CardAssociatedEvent,
    "CardEvolvedEvent": CardEvolvedEvent,
    "AttackDeclaredEvent": AttackDeclaredEvent,
    "DamageDealtEvent": DamageDealtEvent,
    "CardDestroyedEvent": CardDestroyedEvent,
    "ElementsConsumedEvent": ElementsConsumedEvent,
    "ElementsRestoredEvent": ElementsRestoredEvent,
    "TurnStartedEvent": TurnStartedEvent,
    "TurnEndedEvent": TurnEndedEvent,
    "PhaseChangedEvent": PhaseChangedEvent,
    "GameStartedEvent": GameStartedEvent,
    "GameEndedEvent": GameEndedEvent,
    "NoDefenderEvent": NoDefenderEvent,
    "EffectTriggeredEvent": EffectTriggeredEvent,
    "EffectAppliedEvent": EffectAppliedEvent,
}
