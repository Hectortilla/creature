"""
Game Events

Defines all events that can occur during a game.
Events are used for event-driven processing and effect triggers.

All events use Pydantic BaseModel for validation and serialization.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal, Optional, Union
from datetime import datetime

from pydantic import Field, field_serializer

from app.models.game.base import GameBaseModel
from app.models.game.enums import Zone, TurnPhase, DamageType, StatusType


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
    swap_with_supporting_card_id: str = ""


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
    secondary_target_id: str = ""


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


class AttackResolvedEvent(GameEvent):
    """Event fired after base combat damage for one attack/target has resolved."""
    event_type: Literal["AttackResolvedEvent"] = "AttackResolvedEvent"
    attacker_owner_id: str = ""
    attacker_id: str = ""
    target_id: str = ""
    attack_id: int = 0
    attack_name: str = ""
    final_damage: int = 0
    target_destroyed: bool = False
    secondary_target_id: str = ""


class CardDestroyedEvent(GameEvent):
    """Event fired when a card is destroyed (health <= 0)."""
    event_type: Literal["CardDestroyedEvent"] = "CardDestroyedEvent"
    instance_id: str = ""
    owner_id: str = ""
    card_name: str = ""
    destroyed_by: Optional[str] = None


class CardExiledEvent(GameEvent):
    """Event fired when a card is removed from the game instead of sent to graveyard."""
    event_type: Literal["CardExiledEvent"] = "CardExiledEvent"
    instance_id: str = ""
    owner_id: str = ""
    reason: str = ""


class CardHealthChangedEvent(GameEvent):
    """Event fired for non-combat health changes such as DoT or effect damage."""
    event_type: Literal["CardHealthChangedEvent"] = "CardHealthChangedEvent"
    target_id: str = ""
    source_id: str = ""
    delta: int = 0
    new_health: int = 0
    reason: str = ""


class HealingAppliedEvent(GameEvent):
    """Event fired when an effect heals a card."""
    event_type: Literal["HealingAppliedEvent"] = "HealingAppliedEvent"
    target_id: str = ""
    source_id: str = ""
    amount: int = 0
    new_health: int = 0


class StatusAppliedEvent(GameEvent):
    """Event fired when an effect applies a temporary status."""
    event_type: Literal["StatusAppliedEvent"] = "StatusAppliedEvent"
    target_id: str = ""
    source_card_id: str = ""
    source_atom_id: Optional[int] = None
    status_type: StatusType = StatusType.BLOCK_ATTACK
    duration_turns: int = 1
    tick_on: str = "none"
    expires_on: str = "own_turn_end"
    payload: dict[str, Any] = Field(default_factory=dict)


class StatusTickedEvent(GameEvent):
    """Event fired when a status consumes one tick of duration."""
    event_type: Literal["StatusTickedEvent"] = "StatusTickedEvent"
    target_id: str = ""
    status_id: str = ""


class StatusExpiredEvent(GameEvent):
    """Event fired when a status expires or is consumed."""
    event_type: Literal["StatusExpiredEvent"] = "StatusExpiredEvent"
    target_id: str = ""
    status_id: str = ""


class ForcedSwapRequestedEvent(GameEvent):
    """Event fired when a defending player must swap a damaged card."""
    event_type: Literal["ForcedSwapRequestedEvent"] = "ForcedSwapRequestedEvent"
    owner_id: str = ""
    target_card_id: str = ""
    source_card_id: str = ""


class DiceRolledEvent(GameEvent):
    """Event fired when an effect rolls a die."""
    event_type: Literal["DiceRolledEvent"] = "DiceRolledEvent"
    roller_id: str = ""
    faces: int = 6
    result: int = 0
    purpose: str = ""


class CardRevivedEvent(GameEvent):
    """Event fired when a graveyard card swaps back into an active zone."""
    event_type: Literal["CardRevivedEvent"] = "CardRevivedEvent"
    player_id: str = ""
    source_card_id: str = ""
    revived_card_id: str = ""
    target_zone: Zone = Zone.SUPPORTING


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
    AttackResolvedEvent,
    CardDestroyedEvent,
    CardExiledEvent,
    CardHealthChangedEvent,
    HealingAppliedEvent,
    StatusAppliedEvent,
    StatusTickedEvent,
    StatusExpiredEvent,
    ForcedSwapRequestedEvent,
    DiceRolledEvent,
    CardRevivedEvent,
    ElementsConsumedEvent,
    ElementsRestoredEvent,
    TurnStartedEvent,
    TurnEndedEvent,
    PhaseChangedEvent,
    GameStartedEvent,
    GameEndedEvent,
    NoDefenderEvent,
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


# Derived from the single registry above so it can never drift out of sync.
__all__ = [
    "GameEvent",
    *EVENT_TYPES.keys(),
    "GameEventUnion",
    "EVENT_TYPES",
]
