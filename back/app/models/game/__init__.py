"""
Game State Models

Core data structures for representing game state, including cards,
players, zones, and the overall game state.

All models use Pydantic BaseModel for validation and serialization.
Uses @computed_field for derived properties to include in serialization.
"""

from __future__ import annotations

import uuid
from typing import Any, Optional
from datetime import datetime
from enum import Enum, auto
from pydantic import BaseModel, Field, ConfigDict, field_serializer, computed_field


# ============================================================================
# Game Enumerations
# ============================================================================

class Zone(Enum):
    """
    Zones in the game. Each player has their own instance of each zone.
    
    - DECK: Contains 22 cards at game start, cards are drawn from here
    - HAND: Cards held by player, can be played from here
    - SUPPORTING: Max 3 cards, cannot attack but contribute elements/skills
    - ATTACKING: Max 2 cards, can attack and contribute elements/skills
    - GRAVEYARD: Destroyed cards go here, no effect
    """
    DECK = auto()
    HAND = auto()
    SUPPORTING = auto()
    ATTACKING = auto()
    GRAVEYARD = auto()


class TurnPhase(Enum):
    """
    Turn phases in order of execution.
    
    Each player's turn follows this sequence:
    1. DRAW - Draw cards from deck
    2. PLACEMENT - Place cards from hand to supporting zone
    3. PROMOTION - Move cards from supporting to attacking zone
    4. SWAP - Swap supporting and attacking cards
    5. ASSOCIATION - Apply association cards
    6. EVOLUTION - Evolve eligible creatures
    7. ATTACK - Perform attacks with attacking creatures
    """
    DRAW = auto()
    PLACEMENT = auto()
    PROMOTION = auto()
    SWAP = auto()
    ASSOCIATION = auto()
    EVOLUTION = auto()
    ATTACK = auto()
    
    @classmethod
    def get_order(cls) -> list["TurnPhase"]:
        """Get phases in execution order."""
        return [
            cls.DRAW,
            cls.PLACEMENT,
            cls.PROMOTION,
            cls.SWAP,
            cls.ASSOCIATION,
            cls.EVOLUTION,
            cls.ATTACK,
        ]
    
    def next_phase(self) -> "TurnPhase | None":
        """Get the next phase, or None if this is the last phase."""
        order = self.get_order()
        idx = order.index(self)
        if idx < len(order) - 1:
            return order[idx + 1]
        return None


class DamageType(Enum):
    """
    Types of damage in the game.
    
    - PHYSICAL: Reduced by physical defense
    - MAGICAL: Reduced by magical defense
    """
    PHYSICAL = auto()
    MAGICAL = auto()


class GameStatus(Enum):
    """
    Overall game status.
    
    - WAITING: Game created, waiting for players
    - STARTING: Game is initializing
    - IN_PROGRESS: Game is actively being played
    - PAUSED: Game is paused (e.g., waiting for forced defend)
    - FINISHED: Game has ended
    """
    WAITING = auto()
    STARTING = auto()
    IN_PROGRESS = auto()
    PAUSED = auto()
    FINISHED = auto()


class CardStatus(Enum):
    """
    Status flags for cards in active zones.
    
    - READY: Card is ready and contributing normally
    - SWAPPED: Card was swapped this turn, no element contribution
    - EXHAUSTED: Card has attacked this turn
    - ASSOCIATED: Card is being used as an association
    """
    READY = auto()
    SWAPPED = auto()
    EXHAUSTED = auto()
    ASSOCIATED = auto()


class EffectTiming(Enum):
    """
    When effects trigger.
    
    - IMMEDIATE: Triggers immediately when condition is met
    - START_OF_TURN: Triggers at the start of owner's turn
    - END_OF_TURN: Triggers at the end of owner's turn
    - ON_ATTACK: Triggers when this card attacks
    - ON_DEFEND: Triggers when this card is attacked
    - ON_DAMAGE: Triggers when this card takes damage
    - ON_DESTROY: Triggers when this card is destroyed
    - ON_PLAY: Triggers when this card enters play
    - ON_PROMOTE: Triggers when this card moves to attacking zone
    - PASSIVE: Always active while card is in active zone
    """
    IMMEDIATE = auto()
    START_OF_TURN = auto()
    END_OF_TURN = auto()
    ON_ATTACK = auto()
    ON_DEFEND = auto()
    ON_DAMAGE = auto()
    ON_DESTROY = auto()
    ON_PLAY = auto()
    ON_PROMOTE = auto()
    PASSIVE = auto()


# ============================================================================
# Base Model
# ============================================================================

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
        populate_by_name=True,
        validate_assignment=True,
        arbitrary_types_allowed=True,
        use_enum_values=False,
    )


# ============================================================================
# Element & Attack Models
# ============================================================================

class ElementContribution(GameBaseModel):
    """
    Represents element contribution from a card.
    Used for element costs, contributions, and any element+amount pair.
    """
    element_id: int
    amount: int


class AttackDefinition(GameBaseModel):
    """
    Represents an attack that a creature can perform.
    """
    attack_id: int
    name: str
    base_damage: int
    damage_type: DamageType
    element_id: int
    element_cost: list[ElementContribution] = []
    effect_id: Optional[str] = None
    description: Optional[str] = None
    
    @field_serializer('damage_type')
    def serialize_damage_type(self, value: DamageType) -> str:
        return value.name


# ============================================================================
# Card Model
# ============================================================================

class GameCard(GameBaseModel):
    """
    Represents a card instance in the game.
    
    This is distinct from the database Card model - this represents
    a specific instance of a card during gameplay with runtime state.
    """
    instance_id: str
    card_id: int
    owner_id: str
    name: str
    
    # Combat stats
    max_health: int
    current_health: int
    physical_defense: int
    magical_defense: int
    
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
               max_health: int, physical_defense: int, magical_defense: int,
               **kwargs) -> "GameCard":
        """Factory method to create a new game card instance."""
        return cls(
            instance_id=str(uuid.uuid4()),
            card_id=card_id,
            owner_id=owner_id,
            name=name,
            max_health=max_health,
            current_health=max_health,
            physical_defense=physical_defense,
            magical_defense=magical_defense,
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
        self.current_health = min(self.max_health, self.current_health + amount)
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


# ============================================================================
# Zone & Element Pool Models
# ============================================================================

class ZoneState(GameBaseModel):
    """
    Represents the state of a single zone for a player.
    """
    zone: Zone
    owner_id: str
    card_ids: list[str] = []
    max_capacity: Optional[int] = None
    
    @field_serializer('zone')
    def serialize_zone(self, value: Zone) -> str:
        return value.name
    
    @computed_field
    @property
    def is_full(self) -> bool:
        """Check if the zone is at capacity."""
        if self.max_capacity is None:
            return False
        return len(self.card_ids) >= self.max_capacity
    
    def model_post_init(self, __context: Any) -> None:
        """Set capacity limits based on zone type."""
        if self.max_capacity is None:
            if self.zone == Zone.SUPPORTING:
                object.__setattr__(self, 'max_capacity', 3)
            elif self.zone == Zone.ATTACKING:
                object.__setattr__(self, 'max_capacity', 2)
    
    def available_slots(self) -> int:
        """Get the number of available slots."""
        if self.max_capacity is None:
            return float('inf')
        return max(0, self.max_capacity - len(self.card_ids))
    
    def add_card(self, card_id: str) -> bool:
        """Add a card to the zone. Returns False if zone is full."""
        if self.is_full:
            return False
        self.card_ids.append(card_id)
        return True
    
    def remove_card(self, card_id: str) -> bool:
        """Remove a card from the zone. Returns False if card not found."""
        if card_id in self.card_ids:
            self.card_ids.remove(card_id)
            return True
        return False
    
    def has_card(self, card_id: str) -> bool:
        """Check if a card is in this zone."""
        return card_id in self.card_ids


class ElementPool(GameBaseModel):
    """
    Tracks available elements for a player.
    """
    elements: dict[int, int] = {}
    max_elements: dict[int, int] = {}
    
    def get_available(self, element_id: int) -> int:
        """Get available amount of an element."""
        return self.elements.get(element_id, 0)
    
    def consume(self, element_id: int, amount: int) -> bool:
        """Consume elements. Returns False if not enough available."""
        available = self.get_available(element_id)
        if available < amount:
            return False
        self.elements[element_id] = available - amount
        return True
    
    def consume_multiple(self, costs: list[ElementContribution]) -> bool:
        """
        Consume multiple element costs. 
        All-or-nothing - either all costs are paid or none are.
        """
        for cost in costs:
            if self.get_available(cost.element_id) < cost.amount:
                return False
        for cost in costs:
            self.consume(cost.element_id, cost.amount)
        return True
    
    def add(self, element_id: int, amount: int) -> None:
        """Add elements to the pool."""
        current = self.elements.get(element_id, 0)
        self.elements[element_id] = current + amount
        max_current = self.max_elements.get(element_id, 0)
        self.max_elements[element_id] = max(max_current, current + amount)
    
    def restore(self) -> None:
        """Restore elements to their maximum values."""
        self.elements = self.max_elements.copy()
    
    def recalculate_from_cards(self, cards: list[GameCard]) -> None:
        """Recalculate element pool from contributing cards."""
        self.elements.clear()
        self.max_elements.clear()
        
        for card in cards:
            if card.zone in (Zone.SUPPORTING, Zone.ATTACKING):
                for contrib in card.get_element_contribution():
                    current = self.elements.get(contrib.element_id, 0)
                    self.elements[contrib.element_id] = current + contrib.amount
        
        self.max_elements = self.elements.copy()


# ============================================================================
# Player & Game State Models
# ============================================================================

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


class GameConfiguration(GameBaseModel):
    """
    Configuration options for a game.
    """
    deck_size: int = 22
    initial_draw: int = 4
    normal_draw: int = 1
    supporting_zone_size: int = 3
    attacking_zone_size: int = 2


class GameState(GameBaseModel):
    """
    Complete state of a game.
    """
    game_id: str
    players: dict[str, PlayerState]
    cards: dict[str, GameCard] = {}
    active_player_id: Optional[str] = None
    turn_number: int = 0
    current_phase: TurnPhase = TurnPhase.DRAW
    status: GameStatus = GameStatus.WAITING
    winner_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    event_log: list[dict[str, Any]] = []
    pending_action: Optional[str] = None
    config: GameConfiguration = Field(default_factory=GameConfiguration)
    
    @field_serializer('current_phase')
    def serialize_phase(self, value: TurnPhase) -> str:
        return value.name
    
    @field_serializer('status')
    def serialize_status(self, value: GameStatus) -> str:
        return value.name
    
    @field_serializer('created_at')
    def serialize_created_at(self, value: datetime) -> str:
        return value.isoformat()
    
    @classmethod
    def create(cls, player1_id: str, player1_name: str,
               player2_id: str, player2_name: str,
               config: Optional[GameConfiguration] = None) -> "GameState":
        """Factory method to create a new game."""
        return cls(
            game_id=str(uuid.uuid4()),
            players={
                player1_id: PlayerState(player_id=player1_id, name=player1_name),
                player2_id: PlayerState(player_id=player2_id, name=player2_name),
            },
            config=config or GameConfiguration(),
        )
    
    def get_player(self, player_id: str) -> PlayerState:
        """Get a player's state."""
        return self.players[player_id]
    
    def get_active_player(self) -> Optional[PlayerState]:
        """Get the active player's state."""
        if self.active_player_id:
            return self.players[self.active_player_id]
        return None
    
    def get_opponent(self, player_id: str) -> PlayerState:
        """Get the opponent of a given player."""
        for pid, player in self.players.items():
            if pid != player_id:
                return player
        raise ValueError(f"No opponent found for player {player_id}")
    
    def get_card(self, instance_id: str) -> Optional[GameCard]:
        """Get a card by instance ID."""
        return self.cards.get(instance_id)
    
    def get_cards_in_zone(self, player_id: str, zone: Zone) -> list[GameCard]:
        """Get all cards in a specific zone for a player."""
        zone_state = self.players[player_id].zones[zone.name]
        return [self.cards[cid] for cid in zone_state.card_ids if cid in self.cards]
    
    def add_card(self, card: GameCard) -> None:
        """Add a card to the game."""
        self.cards[card.instance_id] = card
        player = self.players[card.owner_id]
        player.zones[card.zone.name].add_card(card.instance_id)
    
    def move_card(self, card_id: str, to_zone: Zone) -> bool:
        """Move a card to a different zone. Returns False if not possible."""
        card = self.cards.get(card_id)
        if not card:
            return False
        
        player = self.players[card.owner_id]
        from_zone = card.zone
        
        if not player.zones[from_zone.name].remove_card(card_id):
            return False
        
        if not player.zones[to_zone.name].add_card(card_id):
            player.zones[from_zone.name].add_card(card_id)
            return False
        
        card.zone = to_zone
        card.turns_in_zone = 0
        return True
    
    def is_first_turn(self, player_id: str) -> bool:
        """Check if this is the first turn for a player."""
        return self.players[player_id].turn_count == 0
    
    def is_second_turn(self, player_id: str) -> bool:
        """Check if this is the second turn for a player."""
        return self.players[player_id].turn_count == 1
    
    def recalculate_elements(self, player_id: str) -> None:
        """Recalculate element pool for a player based on their active cards."""
        player = self.players[player_id]
        active_cards = [
            self.cards[cid] for cid in player.get_active_cards()
            if cid in self.cards
        ]
        player.element_pool.recalculate_from_cards(active_cards)
    
    def log_event(self, event_data: dict[str, Any]) -> None:
        """Add an event to the event log."""
        event_data["timestamp"] = datetime.utcnow().isoformat()
        event_data["turn"] = self.turn_number
        event_data["phase"] = self.current_phase.name
        self.event_log.append(event_data)
    
    def check_game_end(self) -> Optional[str]:
        """
        Check if the game has ended.
        Returns the winner's player_id if game is over, None otherwise.
        """
        for player_id, player in self.players.items():
            total_cards = (
                len(player.zones[Zone.DECK.name].card_ids) +
                len(player.zones[Zone.HAND.name].card_ids) +
                len(player.get_active_cards())
            )
            if total_cards == 0:
                opponent = self.get_opponent(player_id)
                return opponent.player_id
        return None


# ============================================================================
# Result Models
# ============================================================================

class AttackResult(GameBaseModel):
    """
    Result of an attack calculation.
    """
    attacker_id: str
    target_id: str
    attack_id: int
    base_damage: int
    element_bonus: int
    defense_reduction: int
    final_damage: int
    target_destroyed: bool
    attacker_damaged: bool = False
    attacker_damage: int = 0


__all__ = [
    # Enums
    "Zone",
    "TurnPhase",
    "DamageType",
    "GameStatus",
    "CardStatus",
    "EffectTiming",
    # Models
    "GameBaseModel",
    "ElementContribution",
    "AttackDefinition",
    "GameCard",
    "ZoneState",
    "ElementPool",
    "PlayerState",
    "GameConfiguration",
    "GameState",
    "AttackResult",
]

