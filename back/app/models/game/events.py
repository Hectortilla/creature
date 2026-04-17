"""
Game Events

Defines all events that can occur during a game.
Events are used for event-driven processing and effect triggers.

All events use Pydantic BaseModel for validation and serialization.
"""

from __future__ import annotations

from typing import Annotated, Literal, Optional, Union
from datetime import datetime

from pydantic import Field, field_serializer

from app.models.game.base import GameBaseModel
from app.models.game.enums import Zone, TurnPhase, DamageType


class GameEvent(GameBaseModel):
    """
    Base class for all game events.
    
    Uses Pydantic's model_dump() for serialization.
    Subclasses define event_type as a Literal field for discriminated union support.
    """
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    game_id: Optional[str] = None
    event_type: str
    
    @field_serializer('timestamp')
    def serialize_timestamp(self, value: datetime) -> str:
        return value.isoformat()


# ============================================================================
# Card Movement Events
# ============================================================================

class CardDrawnEvent(GameEvent):
    """Event fired when a card is drawn from deck to hand."""
    event_type: Literal["CardDrawnEvent"] = "CardDrawnEvent"
    player_id: str = ""
    instance_id: str = ""
    card_id: int = 0
    cards_remaining: int = 0


class CardPlayedEvent(GameEvent):
    """Event fired when a card is played from hand to supporting zone."""
    event_type: Literal["CardPlayedEvent"] = "CardPlayedEvent"
    player_id: str = ""
    instance_id: str = ""
    card_id: int = 0
    card_name: str = ""


class CardPromotedEvent(GameEvent):
    """Event fired when a card is promoted from supporting to attacking zone."""
    event_type: Literal["CardPromotedEvent"] = "CardPromotedEvent"
    player_id: str = ""
    instance_id: str = ""
    card_id: int = 0
    card_name: str = ""


class CardSwappedEvent(GameEvent):
    """Event fired when two cards are swapped between zones."""
    event_type: Literal["CardSwappedEvent"] = "CardSwappedEvent"
    player_id: str = ""
    supporting_card_id: str = ""
    attacking_card_id: str = ""


# ============================================================================
# Association & Evolution Events
# ============================================================================

class CardAssociatedEvent(GameEvent):
    """Event fired when a card is associated with another card."""
    event_type: Literal["CardAssociatedEvent"] = "CardAssociatedEvent"
    player_id: str = ""
    association_card_id: str = ""
    card_id: int = 0
    target_card_id: str = ""
    source_zone: Optional[Zone] = None


class CardEvolvedEvent(GameEvent):
    """Event fired when a card evolves."""
    event_type: Literal["CardEvolvedEvent"] = "CardEvolvedEvent"
    player_id: str = ""
    base_card_id: str = ""
    evolution_card_id: str = ""
    card_id: int = 0
    base_card_name: str = ""
    evolution_card_name: str = ""


# ============================================================================
# Combat Events
# ============================================================================

class AttackDeclaredEvent(GameEvent):
    """Event fired when an attack is declared."""
    event_type: Literal["AttackDeclaredEvent"] = "AttackDeclaredEvent"
    attacker_owner_id: str = ""
    attacker_id: str = ""
    target_id: str = ""
    attack_id: int = 0
    attack_name: str = ""


class DamageDealtEvent(GameEvent):
    """Event fired when damage is dealt to a card."""
    event_type: Literal["DamageDealtEvent"] = "DamageDealtEvent"
    source_id: str = ""
    target_id: str = ""
    damage_type: Optional[DamageType] = None
    base_damage: int = 0
    element_bonus: int = 0
    defense_reduction: int = 0
    final_damage: int = 0
    remaining_health: int = 0


class CardDestroyedEvent(GameEvent):
    """Event fired when a card is destroyed (health <= 0)."""
    event_type: Literal["CardDestroyedEvent"] = "CardDestroyedEvent"
    instance_id: str = ""
    owner_id: str = ""
    card_name: str = ""
    destroyed_by: Optional[str] = None


# ============================================================================
# Element Events
# ============================================================================

class ElementsConsumedEvent(GameEvent):
    """Event fired when elements are consumed for an attack."""
    event_type: Literal["ElementsConsumedEvent"] = "ElementsConsumedEvent"
    player_id: str = ""
    elements: dict[int, int] = {}
    for_attack_id: int = 0


class ElementsRestoredEvent(GameEvent):
    """Event fired when elements are restored at turn start."""
    event_type: Literal["ElementsRestoredEvent"] = "ElementsRestoredEvent"
    player_id: str = ""
    elements: dict[int, int] = {}


# ============================================================================
# Turn & Phase Events
# ============================================================================

class TurnStartedEvent(GameEvent):
    """Event fired at the start of a player's turn."""
    event_type: Literal["TurnStartedEvent"] = "TurnStartedEvent"
    player_id: str = ""
    turn_number: int = 0
    is_first_turn: bool = False


class TurnEndedEvent(GameEvent):
    """Event fired at the end of a player's turn."""
    event_type: Literal["TurnEndedEvent"] = "TurnEndedEvent"
    player_id: str = ""
    turn_number: int = 0


class PhaseChangedEvent(GameEvent):
    """Event fired when the turn phase changes."""
    event_type: Literal["PhaseChangedEvent"] = "PhaseChangedEvent"
    player_id: str = ""
    from_phase: Optional[TurnPhase] = None
    to_phase: Optional[TurnPhase] = None


# ============================================================================
# Game-Level Events
# ============================================================================

class GameStartedEvent(GameEvent):
    """Event fired when a game starts."""
    event_type: Literal["GameStartedEvent"] = "GameStartedEvent"
    player_ids: list[str] = []
    first_player_id: str = ""


class GameEndedEvent(GameEvent):
    """Event fired when the game ends."""
    event_type: Literal["GameEndedEvent"] = "GameEndedEvent"
    winner_id: str = ""
    loser_id: str = ""
    reason: str = ""


class NoDefenderEvent(GameEvent):
    """
    Event fired when a player has no defending creatures and is attacked.
    Triggers the forced defend mechanic.
    """
    event_type: Literal["NoDefenderEvent"] = "NoDefenderEvent"
    defender_id: str = ""
    attacker_id: str = ""
    must_defend: bool = False
    game_lost: bool = False
    pending_attacker_card_id: str = ""
    pending_attack_id: int = 0
    pending_attacker_owner_id: str = ""


# ============================================================================
# Effect Events
# ============================================================================

class EffectTriggeredEvent(GameEvent):
    """Event fired when an effect is triggered."""
    event_type: Literal["EffectTriggeredEvent"] = "EffectTriggeredEvent"
    source_card_id: str = ""
    effect_id: str = ""
    effect_name: str = ""
    trigger_reason: str = ""


class EffectAppliedEvent(GameEvent):
    """Event fired when an effect's result is applied."""
    event_type: Literal["EffectAppliedEvent"] = "EffectAppliedEvent"
    effect_id: str = ""
    affected_card_ids: list[str] = []
    description: str = ""


# Single registry — union and dict are both derived from this list
_ALL_EVENT_CLASSES: list[type[GameEvent]] = [
    CardDrawnEvent,
    CardPlayedEvent,
    CardPromotedEvent,
    CardSwappedEvent,
    CardAssociatedEvent,
    CardEvolvedEvent,
    AttackDeclaredEvent,
    DamageDealtEvent,
    CardDestroyedEvent,
    ElementsConsumedEvent,
    ElementsRestoredEvent,
    TurnStartedEvent,
    TurnEndedEvent,
    PhaseChangedEvent,
    GameStartedEvent,
    GameEndedEvent,
    NoDefenderEvent,
    EffectTriggeredEvent,
    EffectAppliedEvent,
]

# Discriminated union for OpenAPI schema generation
GameEventUnion = Annotated[
    Union[tuple(_ALL_EVENT_CLASSES)],
    Field(discriminator="event_type"),
]

# Event type registry for deserialization
EVENT_TYPES: dict[str, type[GameEvent]] = {
    cls.__name__: cls for cls in _ALL_EVENT_CLASSES
}


__all__ = [
    # Base
    "GameEvent",
    # Card Movement
    "CardDrawnEvent",
    "CardPlayedEvent",
    "CardPromotedEvent",
    "CardSwappedEvent",
    # Association & Evolution
    "CardAssociatedEvent",
    "CardEvolvedEvent",
    # Combat
    "AttackDeclaredEvent",
    "DamageDealtEvent",
    "CardDestroyedEvent",
    # Elements
    "ElementsConsumedEvent",
    "ElementsRestoredEvent",
    # Turn & Phase
    "TurnStartedEvent",
    "TurnEndedEvent",
    "PhaseChangedEvent",
    # Game-Level
    "GameStartedEvent",
    "GameEndedEvent",
    "NoDefenderEvent",
    # Effects
    "EffectTriggeredEvent",
    "EffectAppliedEvent",
    # Union
    "GameEventUnion",
    # Registry
    "EVENT_TYPES",
]
