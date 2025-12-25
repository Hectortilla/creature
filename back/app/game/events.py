"""
Game Events

Defines all events that can occur during a game.
Events are used for event-driven processing and effect triggers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime
from abc import ABC

from app.game.enums import Zone, TurnPhase, DamageType


@dataclass
class GameEvent(ABC):
    """
    Base class for all game events.
    
    Attributes:
        timestamp: When the event occurred
        game_id: ID of the game this event belongs to
    """
    timestamp: datetime = field(default_factory=datetime.utcnow)
    game_id: Optional[str] = None
    
    @property
    def event_type(self) -> str:
        """Return the type name of this event."""
        return self.__class__.__name__
    
    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary for logging/serialization."""
        return {
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "game_id": self.game_id,
        }


# ============================================================================
# Card Movement Events
# ============================================================================

@dataclass
class CardDrawnEvent(GameEvent):
    """
    Event fired when a card is drawn from deck to hand.
    
    Attributes:
        player_id: ID of the player who drew the card
        card_id: Instance ID of the card drawn
        cards_remaining: Number of cards remaining in deck
    """
    player_id: str = ""
    card_id: str = ""
    cards_remaining: int = 0
    
    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d.update({
            "player_id": self.player_id,
            "card_id": self.card_id,
            "cards_remaining": self.cards_remaining,
        })
        return d


@dataclass
class CardMovedEvent(GameEvent):
    """
    Event fired when a card moves between zones.
    
    Attributes:
        card_id: Instance ID of the card
        owner_id: ID of the player who owns the card
        from_zone: Zone the card moved from
        to_zone: Zone the card moved to
    """
    card_id: str = ""
    owner_id: str = ""
    from_zone: Optional[Zone] = None
    to_zone: Optional[Zone] = None
    
    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d.update({
            "card_id": self.card_id,
            "owner_id": self.owner_id,
            "from_zone": self.from_zone.name if self.from_zone else None,
            "to_zone": self.to_zone.name if self.to_zone else None,
        })
        return d


@dataclass
class CardPlayedEvent(GameEvent):
    """
    Event fired when a card is played from hand to supporting zone.
    
    Attributes:
        player_id: ID of the player who played the card
        card_id: Instance ID of the card
        card_name: Name of the card (for logging)
    """
    player_id: str = ""
    card_id: str = ""
    card_name: str = ""
    
    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d.update({
            "player_id": self.player_id,
            "card_id": self.card_id,
            "card_name": self.card_name,
        })
        return d


@dataclass
class CardPromotedEvent(GameEvent):
    """
    Event fired when a card is promoted from supporting to attacking zone.
    
    Attributes:
        player_id: ID of the player
        card_id: Instance ID of the card
        card_name: Name of the card
    """
    player_id: str = ""
    card_id: str = ""
    card_name: str = ""
    
    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d.update({
            "player_id": self.player_id,
            "card_id": self.card_id,
            "card_name": self.card_name,
        })
        return d


@dataclass
class CardSwappedEvent(GameEvent):
    """
    Event fired when two cards are swapped between supporting and attacking zones.
    
    Attributes:
        player_id: ID of the player
        supporting_card_id: Card that was in supporting zone
        attacking_card_id: Card that was in attacking zone
    """
    player_id: str = ""
    supporting_card_id: str = ""
    attacking_card_id: str = ""
    
    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d.update({
            "player_id": self.player_id,
            "supporting_card_id": self.supporting_card_id,
            "attacking_card_id": self.attacking_card_id,
        })
        return d


# ============================================================================
# Association & Evolution Events
# ============================================================================

@dataclass
class CardAssociatedEvent(GameEvent):
    """
    Event fired when a card is associated with another card.
    
    Attributes:
        player_id: ID of the player
        association_card_id: Card being used as association
        target_card_id: Card receiving the association
        source_zone: Zone the association card came from
    """
    player_id: str = ""
    association_card_id: str = ""
    target_card_id: str = ""
    source_zone: Optional[Zone] = None
    
    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d.update({
            "player_id": self.player_id,
            "association_card_id": self.association_card_id,
            "target_card_id": self.target_card_id,
            "source_zone": self.source_zone.name if self.source_zone else None,
        })
        return d


@dataclass
class CardEvolvedEvent(GameEvent):
    """
    Event fired when a card evolves.
    
    Attributes:
        player_id: ID of the player
        base_card_id: Card that was evolved (removed)
        evolution_card_id: New evolved card
        base_card_name: Name of the base card
        evolution_card_name: Name of the evolved card
    """
    player_id: str = ""
    base_card_id: str = ""
    evolution_card_id: str = ""
    base_card_name: str = ""
    evolution_card_name: str = ""
    
    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d.update({
            "player_id": self.player_id,
            "base_card_id": self.base_card_id,
            "evolution_card_id": self.evolution_card_id,
            "base_card_name": self.base_card_name,
            "evolution_card_name": self.evolution_card_name,
        })
        return d


# ============================================================================
# Combat Events
# ============================================================================

@dataclass
class AttackDeclaredEvent(GameEvent):
    """
    Event fired when an attack is declared.
    
    Attributes:
        attacker_owner_id: ID of the attacking player
        attacker_id: Instance ID of the attacking card
        target_id: Instance ID of the target card
        attack_id: ID of the attack being used
        attack_name: Name of the attack
    """
    attacker_owner_id: str = ""
    attacker_id: str = ""
    target_id: str = ""
    attack_id: int = 0
    attack_name: str = ""
    
    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d.update({
            "attacker_owner_id": self.attacker_owner_id,
            "attacker_id": self.attacker_id,
            "target_id": self.target_id,
            "attack_id": self.attack_id,
            "attack_name": self.attack_name,
        })
        return d


@dataclass
class DamageDealtEvent(GameEvent):
    """
    Event fired when damage is dealt to a card.
    
    Attributes:
        source_id: Instance ID of the damage source
        target_id: Instance ID of the target
        damage_type: Physical or magical damage
        base_damage: Damage before modifiers
        element_bonus: Bonus from element interactions
        defense_reduction: Damage absorbed by defense
        final_damage: Actual damage dealt
        remaining_health: Target's remaining health
    """
    source_id: str = ""
    target_id: str = ""
    damage_type: Optional[DamageType] = None
    base_damage: int = 0
    element_bonus: int = 0
    defense_reduction: int = 0
    final_damage: int = 0
    remaining_health: int = 0
    
    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d.update({
            "source_id": self.source_id,
            "target_id": self.target_id,
            "damage_type": self.damage_type.name if self.damage_type else None,
            "base_damage": self.base_damage,
            "element_bonus": self.element_bonus,
            "defense_reduction": self.defense_reduction,
            "final_damage": self.final_damage,
            "remaining_health": self.remaining_health,
        })
        return d


@dataclass
class CardDestroyedEvent(GameEvent):
    """
    Event fired when a card is destroyed (health <= 0).
    
    Attributes:
        card_id: Instance ID of the destroyed card
        owner_id: ID of the card's owner
        card_name: Name of the destroyed card
        destroyed_by: Instance ID of the card that destroyed it (if any)
    """
    card_id: str = ""
    owner_id: str = ""
    card_name: str = ""
    destroyed_by: Optional[str] = None
    
    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d.update({
            "card_id": self.card_id,
            "owner_id": self.owner_id,
            "card_name": self.card_name,
            "destroyed_by": self.destroyed_by,
        })
        return d


# ============================================================================
# Element Events
# ============================================================================

@dataclass
class ElementsConsumedEvent(GameEvent):
    """
    Event fired when elements are consumed for an attack.
    
    Attributes:
        player_id: ID of the player
        elements: Dict of element_id -> amount consumed
        for_attack_id: ID of the attack these elements were used for
    """
    player_id: str = ""
    elements: dict[int, int] = field(default_factory=dict)
    for_attack_id: int = 0
    
    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d.update({
            "player_id": self.player_id,
            "elements": self.elements,
            "for_attack_id": self.for_attack_id,
        })
        return d


@dataclass
class ElementsRestoredEvent(GameEvent):
    """
    Event fired when elements are restored at turn start.
    
    Attributes:
        player_id: ID of the player
        elements: Dict of element_id -> amount restored
    """
    player_id: str = ""
    elements: dict[int, int] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d.update({
            "player_id": self.player_id,
            "elements": self.elements,
        })
        return d


# ============================================================================
# Turn & Phase Events
# ============================================================================

@dataclass
class TurnStartedEvent(GameEvent):
    """
    Event fired at the start of a player's turn.
    
    Attributes:
        player_id: ID of the active player
        turn_number: Current turn number
        is_first_turn: Whether this is the player's first turn
    """
    player_id: str = ""
    turn_number: int = 0
    is_first_turn: bool = False
    
    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d.update({
            "player_id": self.player_id,
            "turn_number": self.turn_number,
            "is_first_turn": self.is_first_turn,
        })
        return d


@dataclass
class TurnEndedEvent(GameEvent):
    """
    Event fired at the end of a player's turn.
    
    Attributes:
        player_id: ID of the player whose turn ended
        turn_number: Turn number that ended
    """
    player_id: str = ""
    turn_number: int = 0
    
    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d.update({
            "player_id": self.player_id,
            "turn_number": self.turn_number,
        })
        return d


@dataclass
class PhaseChangedEvent(GameEvent):
    """
    Event fired when the turn phase changes.
    
    Attributes:
        player_id: ID of the active player
        from_phase: Previous phase
        to_phase: New phase
    """
    player_id: str = ""
    from_phase: Optional[TurnPhase] = None
    to_phase: Optional[TurnPhase] = None
    
    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d.update({
            "player_id": self.player_id,
            "from_phase": self.from_phase.name if self.from_phase else None,
            "to_phase": self.to_phase.name if self.to_phase else None,
        })
        return d


# ============================================================================
# Game-Level Events
# ============================================================================

@dataclass
class GameStartedEvent(GameEvent):
    """
    Event fired when a game starts.
    
    Attributes:
        player_ids: IDs of all players in the game
        first_player_id: ID of the player who goes first
    """
    player_ids: list[str] = field(default_factory=list)
    first_player_id: str = ""
    
    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d.update({
            "player_ids": self.player_ids,
            "first_player_id": self.first_player_id,
        })
        return d


@dataclass
class GameEndedEvent(GameEvent):
    """
    Event fired when the game ends.
    
    Attributes:
        winner_id: ID of the winning player
        loser_id: ID of the losing player
        reason: Reason for the game ending
    """
    winner_id: str = ""
    loser_id: str = ""
    reason: str = ""
    
    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d.update({
            "winner_id": self.winner_id,
            "loser_id": self.loser_id,
            "reason": self.reason,
        })
        return d


@dataclass
class NoDefenderEvent(GameEvent):
    """
    Event fired when a player has no defending creatures and is attacked.
    
    This triggers the forced defend mechanic where the player must move
    a supporting creature to the attacking zone.
    
    Attributes:
        defender_id: ID of the player who must defend
        attacker_id: ID of the attacking player
        must_defend: Whether the defender must move a creature (has supporting cards)
        game_lost: Whether the defender lost (no cards to defend with)
    """
    defender_id: str = ""
    attacker_id: str = ""
    must_defend: bool = False
    game_lost: bool = False
    
    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d.update({
            "defender_id": self.defender_id,
            "attacker_id": self.attacker_id,
            "must_defend": self.must_defend,
            "game_lost": self.game_lost,
        })
        return d


# ============================================================================
# Effect Events
# ============================================================================

@dataclass
class EffectTriggeredEvent(GameEvent):
    """
    Event fired when an effect is triggered.
    
    Attributes:
        source_card_id: Card that has the effect
        effect_id: ID of the effect
        effect_name: Name of the effect
        trigger_reason: What triggered the effect
    """
    source_card_id: str = ""
    effect_id: str = ""
    effect_name: str = ""
    trigger_reason: str = ""
    
    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d.update({
            "source_card_id": self.source_card_id,
            "effect_id": self.effect_id,
            "effect_name": self.effect_name,
            "trigger_reason": self.trigger_reason,
        })
        return d


@dataclass
class EffectAppliedEvent(GameEvent):
    """
    Event fired when an effect's result is applied.
    
    Attributes:
        effect_id: ID of the effect
        affected_card_ids: Cards affected by the effect
        description: Description of what happened
    """
    effect_id: str = ""
    affected_card_ids: list[str] = field(default_factory=list)
    description: str = ""
    
    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d.update({
            "effect_id": self.effect_id,
            "affected_card_ids": self.affected_card_ids,
            "description": self.description,
        })
        return d


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

