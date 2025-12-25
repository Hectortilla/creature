"""
Game State Models

Core data structures for representing game state, including cards,
players, zones, and the overall game state.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime

from app.game.enums import Zone, TurnPhase, GameStatus, CardStatus, DamageType


@dataclass
class ElementContribution:
    """
    Represents element contribution from a card.
    
    Attributes:
        element_id: The ID of the element being contributed
        amount: The amount of that element contributed
    """
    element_id: int
    amount: int


@dataclass
class AttackDefinition:
    """
    Represents an attack that a creature can perform.
    
    Attributes:
        attack_id: Database ID of the attack
        name: Display name of the attack
        base_damage: Base damage value before modifiers
        damage_type: Physical or magical damage
        element_id: The element this attack belongs to
        element_cost: Elements required to perform this attack
        effect_id: Optional special effect triggered by this attack
        description: Attack description text
    """
    attack_id: int
    name: str
    base_damage: int
    damage_type: DamageType
    element_id: int
    element_cost: list[ElementContribution] = field(default_factory=list)
    effect_id: Optional[str] = None
    description: Optional[str] = None


@dataclass
class GameCard:
    """
    Represents a card instance in the game.
    
    This is distinct from the database Card model - this represents
    a specific instance of a card during gameplay with runtime state.
    
    Attributes:
        instance_id: Unique identifier for this card instance
        card_id: Database ID of the card template
        owner_id: ID of the player who owns this card
        name: Display name of the card
        
        # Combat stats
        max_health: Maximum health points
        current_health: Current health points
        physical_defense: Defense against physical damage
        magical_defense: Defense against magical damage
        
        # Elements
        element_ids: List of element IDs this card belongs to
        element_contribution: Elements this card contributes when active
        
        # Abilities
        attacks: Available attacks for this creature
        skill_ids: Passive skill IDs (always active in active zones)
        association_ids: Cards that can be associated with this card
        
        # Evolution
        is_evolution: Whether this card is an evolution
        evolves_from_id: Card ID this can evolve from (if evolution)
        
        # Runtime state
        zone: Current zone the card is in
        status: Current status flags
        turns_in_zone: Number of full turns spent in current zone
        associations: List of cards associated with this card
        has_attacked_this_turn: Whether the card has attacked this turn
        swapped_this_turn: Whether the card was swapped this turn
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
    element_ids: list[int] = field(default_factory=list)
    element_contribution: list[ElementContribution] = field(default_factory=list)
    
    # Abilities
    attacks: list[AttackDefinition] = field(default_factory=list)
    skill_ids: list[int] = field(default_factory=list)
    association_ids: list[int] = field(default_factory=list)
    
    # Evolution
    is_evolution: bool = False
    evolves_from_id: Optional[int] = None
    
    # Runtime state
    zone: Zone = Zone.DECK
    status: CardStatus = CardStatus.READY
    turns_in_zone: int = 0
    associations: list[str] = field(default_factory=list)  # instance_ids
    has_attacked_this_turn: bool = False
    swapped_this_turn: bool = False
    
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
    
    def is_alive(self) -> bool:
        """Check if the card is still alive."""
        return self.current_health > 0
    
    def can_attack(self) -> bool:
        """Check if the card can attack."""
        return (
            self.zone == Zone.ATTACKING
            and not self.has_attacked_this_turn
            and self.status != CardStatus.ASSOCIATED
        )
    
    def can_promote(self) -> bool:
        """Check if the card can be promoted to attacking zone."""
        return (
            self.zone == Zone.SUPPORTING
            and self.turns_in_zone >= 1  # Must have spent at least 1 full turn
            and self.status != CardStatus.ASSOCIATED
        )
    
    def can_evolve(self) -> bool:
        """Check if the card can be evolved."""
        return (
            self.zone in (Zone.SUPPORTING, Zone.ATTACKING)
            and self.turns_in_zone >= 1
            and self.status != CardStatus.ASSOCIATED
        )
    
    def get_element_contribution(self) -> list[ElementContribution]:
        """Get element contribution, considering status."""
        if self.swapped_this_turn or self.status == CardStatus.ASSOCIATED:
            return []
        return self.element_contribution
    
    def apply_damage(self, amount: int) -> int:
        """
        Apply damage to the card.
        
        Returns the actual damage dealt (after any reductions).
        """
        actual_damage = max(0, amount)
        self.current_health -= actual_damage
        return actual_damage
    
    def heal(self, amount: int) -> int:
        """
        Heal the card.
        
        Returns the actual healing done.
        """
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


@dataclass
class ZoneState:
    """
    Represents the state of a single zone for a player.
    
    Attributes:
        zone: The zone type
        owner_id: The player who owns this zone
        card_ids: List of card instance IDs in this zone
        max_capacity: Maximum number of cards allowed (None = unlimited)
    """
    zone: Zone
    owner_id: str
    card_ids: list[str] = field(default_factory=list)
    max_capacity: Optional[int] = None
    
    def __post_init__(self):
        """Set capacity limits based on zone type."""
        if self.max_capacity is None:
            if self.zone == Zone.SUPPORTING:
                self.max_capacity = 3
            elif self.zone == Zone.ATTACKING:
                self.max_capacity = 2
            # DECK, HAND, GRAVEYARD have no limit
    
    def is_full(self) -> bool:
        """Check if the zone is at capacity."""
        if self.max_capacity is None:
            return False
        return len(self.card_ids) >= self.max_capacity
    
    def available_slots(self) -> int:
        """Get the number of available slots."""
        if self.max_capacity is None:
            return float('inf')
        return max(0, self.max_capacity - len(self.card_ids))
    
    def add_card(self, card_id: str) -> bool:
        """Add a card to the zone. Returns False if zone is full."""
        if self.is_full():
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


@dataclass
class ElementPool:
    """
    Tracks available elements for a player.
    
    Attributes:
        elements: Mapping of element_id to available amount
        max_elements: Mapping of element_id to maximum (contributed) amount
    """
    elements: dict[int, int] = field(default_factory=dict)
    max_elements: dict[int, int] = field(default_factory=dict)
    
    def get_available(self, element_id: int) -> int:
        """Get available amount of an element."""
        return self.elements.get(element_id, 0)
    
    def consume(self, element_id: int, amount: int) -> bool:
        """
        Consume elements. Returns False if not enough available.
        """
        available = self.get_available(element_id)
        if available < amount:
            return False
        self.elements[element_id] = available - amount
        return True
    
    def consume_multiple(self, costs: list[ElementContribution]) -> bool:
        """
        Consume multiple element costs. Returns False if any cost can't be paid.
        All-or-nothing - either all costs are paid or none are.
        """
        # First check if all costs can be paid
        for cost in costs:
            if self.get_available(cost.element_id) < cost.amount:
                return False
        
        # All checks passed, consume all
        for cost in costs:
            self.consume(cost.element_id, cost.amount)
        return True
    
    def add(self, element_id: int, amount: int) -> None:
        """Add elements to the pool."""
        current = self.elements.get(element_id, 0)
        self.elements[element_id] = current + amount
        
        # Update max if this is a contribution
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


@dataclass
class PlayerState:
    """
    Represents a player's state in the game.
    
    Attributes:
        player_id: Unique identifier for this player
        name: Display name
        turn_count: Number of turns this player has taken
        element_pool: Available elements for attacks
        zones: Player's zones
        has_passed_phase: Whether player has passed the current phase
    """
    player_id: str
    name: str
    turn_count: int = 0
    element_pool: ElementPool = field(default_factory=ElementPool)
    zones: dict[Zone, ZoneState] = field(default_factory=dict)
    has_passed_phase: bool = False
    
    def __post_init__(self):
        """Initialize zones if not provided."""
        if not self.zones:
            self.zones = {
                zone: ZoneState(zone=zone, owner_id=self.player_id)
                for zone in Zone
            }
    
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


@dataclass
class GameState:
    """
    Complete state of a game.
    
    Attributes:
        game_id: Unique identifier for this game
        players: Mapping of player_id to PlayerState
        cards: Mapping of instance_id to GameCard
        active_player_id: ID of the player whose turn it is
        turn_number: Current turn number (increments each time a player takes a turn)
        current_phase: Current turn phase
        status: Overall game status
        winner_id: ID of the winning player (if game is finished)
        created_at: When the game was created
        event_log: Log of all game events
        pending_action: Action waiting for response (e.g., forced defend)
        config: Game configuration (deck size, draw amounts, etc.)
    """
    game_id: str
    players: dict[str, PlayerState]
    cards: dict[str, GameCard] = field(default_factory=dict)
    active_player_id: Optional[str] = None
    turn_number: int = 0
    current_phase: TurnPhase = TurnPhase.DRAW
    status: GameStatus = GameStatus.WAITING
    winner_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    event_log: list[dict[str, Any]] = field(default_factory=list)
    pending_action: Optional[str] = None
    config: "GameConfiguration" = field(default_factory=lambda: GameConfiguration())
    
    @classmethod
    def create(cls, player1_id: str, player1_name: str,
               player2_id: str, player2_name: str,
               config: Optional["GameConfiguration"] = None) -> "GameState":
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
        zone_state = self.players[player_id].zones[zone]
        return [self.cards[cid] for cid in zone_state.card_ids if cid in self.cards]
    
    def add_card(self, card: GameCard) -> None:
        """Add a card to the game."""
        self.cards[card.instance_id] = card
        player = self.players[card.owner_id]
        player.zones[card.zone].add_card(card.instance_id)
    
    def move_card(self, card_id: str, to_zone: Zone) -> bool:
        """
        Move a card to a different zone.
        
        Returns False if the move is not possible.
        """
        card = self.cards.get(card_id)
        if not card:
            return False
        
        player = self.players[card.owner_id]
        from_zone = card.zone
        
        # Remove from current zone
        if not player.zones[from_zone].remove_card(card_id):
            return False
        
        # Add to new zone
        if not player.zones[to_zone].add_card(card_id):
            # Rollback
            player.zones[from_zone].add_card(card_id)
            return False
        
        # Update card state
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
            # Check if player has no cards at all (deck + hand + active)
            total_cards = (
                len(player.zones[Zone.DECK].card_ids) +
                len(player.zones[Zone.HAND].card_ids) +
                len(player.get_active_cards())
            )
            if total_cards == 0:
                # This player loses
                opponent = self.get_opponent(player_id)
                return opponent.player_id
        
        return None


@dataclass
class AttackResult:
    """
    Result of an attack calculation.
    
    Attributes:
        attacker_id: Instance ID of the attacking card
        target_id: Instance ID of the target card
        attack_id: ID of the attack used
        base_damage: Base damage before modifiers
        element_bonus: Bonus/penalty from element interactions
        defense_reduction: Damage reduced by defense
        final_damage: Final damage dealt
        target_destroyed: Whether the target was destroyed
        attacker_damaged: Whether the attacker took damage (negative result)
        attacker_damage: Damage dealt to attacker (if any)
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


@dataclass
class GameConfiguration:
    """
    Configuration options for a game.
    
    Attributes:
        deck_size: Number of cards in each player's deck
        initial_draw: Number of cards drawn on first turn
        normal_draw: Number of cards drawn on subsequent turns
        supporting_zone_size: Maximum cards in supporting zone
        attacking_zone_size: Maximum cards in attacking zone
    """
    deck_size: int = 22
    initial_draw: int = 4
    normal_draw: int = 1
    supporting_zone_size: int = 3
    attacking_zone_size: int = 2

