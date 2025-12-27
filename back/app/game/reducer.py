"""
Game Reducer

Pure functions that apply events to game state.
The reducer is the ONLY place where state mutations happen.

Pattern:
    new_state = apply_event(state, event)

All functions are pure - they don't modify the input state,
they return a new state with the changes applied.
"""

from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING

from app.models.game import (
    Zone,
    GameStatus,
    CardStatus,
    GameEvent,
    CardDrawnEvent,
    CardMovedEvent,
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
)

if TYPE_CHECKING:
    from app.models.game import GameState


def apply_event(state: "GameState", event: GameEvent) -> "GameState":
    """
    Apply a single event to the game state.
    
    This is the main entry point for the reducer.
    Returns a new state with the event applied.
    
    Args:
        state: Current game state (not modified)
        event: Event to apply
    
    Returns:
        New game state with event applied
    """
    # Create a deep copy to ensure immutability
    new_state = deepcopy(state)
    
    # Dispatch to specific handler
    if isinstance(event, CardDrawnEvent):
        return _apply_card_drawn(new_state, event)
    elif isinstance(event, CardMovedEvent):
        return _apply_card_moved(new_state, event)
    elif isinstance(event, CardPlayedEvent):
        return _apply_card_played(new_state, event)
    elif isinstance(event, CardPromotedEvent):
        return _apply_card_promoted(new_state, event)
    elif isinstance(event, CardSwappedEvent):
        return _apply_card_swapped(new_state, event)
    elif isinstance(event, CardAssociatedEvent):
        return _apply_card_associated(new_state, event)
    elif isinstance(event, CardEvolvedEvent):
        return _apply_card_evolved(new_state, event)
    elif isinstance(event, DamageDealtEvent):
        return _apply_damage_dealt(new_state, event)
    elif isinstance(event, CardDestroyedEvent):
        return _apply_card_destroyed(new_state, event)
    elif isinstance(event, ElementsConsumedEvent):
        return _apply_elements_consumed(new_state, event)
    elif isinstance(event, ElementsRestoredEvent):
        return _apply_elements_restored(new_state, event)
    elif isinstance(event, TurnStartedEvent):
        return _apply_turn_started(new_state, event)
    elif isinstance(event, TurnEndedEvent):
        return _apply_turn_ended(new_state, event)
    elif isinstance(event, PhaseChangedEvent):
        return _apply_phase_changed(new_state, event)
    elif isinstance(event, GameStartedEvent):
        return _apply_game_started(new_state, event)
    elif isinstance(event, GameEndedEvent):
        return _apply_game_ended(new_state, event)
    elif isinstance(event, NoDefenderEvent):
        return _apply_no_defender(new_state, event)
    elif isinstance(event, AttackDeclaredEvent):
        return _apply_attack_declared(new_state, event)
    
    # Unknown event type - return state unchanged
    return new_state


def apply_events(state: "GameState", events: list[GameEvent]) -> "GameState":
    """
    Apply multiple events in sequence.
    
    Args:
        state: Initial game state
        events: List of events to apply in order
    
    Returns:
        Final game state after all events applied
    """
    current_state = state
    for event in events:
        current_state = apply_event(current_state, event)
    return current_state


# ============================================================================
# Card Movement Reducers
# ============================================================================

def _apply_card_drawn(state: "GameState", event: CardDrawnEvent) -> "GameState":
    """Apply card drawn event - move card from deck to hand."""
    player = state.players[event.player_id]
    card = state.cards.get(event.card_id)
    
    if card:
        # Remove from deck
        if event.card_id in player.zones[Zone.DECK].card_ids:
            player.zones[Zone.DECK].card_ids.remove(event.card_id)
        
        # Add to hand
        if event.card_id not in player.zones[Zone.HAND].card_ids:
            player.zones[Zone.HAND].card_ids.append(event.card_id)
        
        # Update card zone
        card.zone = Zone.HAND
    
    return state


def _apply_card_moved(state: "GameState", event: CardMovedEvent) -> "GameState":
    """Apply generic card movement event."""
    player = state.players[event.owner_id]
    card = state.cards.get(event.card_id)
    
    if card and event.from_zone and event.to_zone:
        # Remove from source zone
        if event.card_id in player.zones[event.from_zone].card_ids:
            player.zones[event.from_zone].card_ids.remove(event.card_id)
        
        # Add to target zone
        if event.card_id not in player.zones[event.to_zone].card_ids:
            player.zones[event.to_zone].card_ids.append(event.card_id)
        
        # Update card state
        card.zone = event.to_zone
        card.turns_in_zone = 0
    
    return state


def _apply_card_played(state: "GameState", event: CardPlayedEvent) -> "GameState":
    """Apply card played event - move from hand to supporting zone."""
    player = state.players[event.player_id]
    card = state.cards.get(event.card_id)
    
    if card:
        # Remove from hand
        if event.card_id in player.zones[Zone.HAND].card_ids:
            player.zones[Zone.HAND].card_ids.remove(event.card_id)
        
        # Add to supporting zone
        if event.card_id not in player.zones[Zone.SUPPORTING].card_ids:
            player.zones[Zone.SUPPORTING].card_ids.append(event.card_id)
        
        # Update card state
        card.zone = Zone.SUPPORTING
        card.turns_in_zone = 0
        
        # Recalculate elements
        _recalculate_elements(state, event.player_id)
    
    return state


def _apply_card_promoted(state: "GameState", event: CardPromotedEvent) -> "GameState":
    """Apply card promoted event - move from supporting to attacking zone."""
    player = state.players[event.player_id]
    card = state.cards.get(event.card_id)
    
    if card:
        # Remove from supporting
        if event.card_id in player.zones[Zone.SUPPORTING].card_ids:
            player.zones[Zone.SUPPORTING].card_ids.remove(event.card_id)
        
        # Add to attacking
        if event.card_id not in player.zones[Zone.ATTACKING].card_ids:
            player.zones[Zone.ATTACKING].card_ids.append(event.card_id)
        
        # Update card state
        card.zone = Zone.ATTACKING
        card.turns_in_zone = 0
        
        # Recalculate elements
        _recalculate_elements(state, event.player_id)
    
    return state


def _apply_card_swapped(state: "GameState", event: CardSwappedEvent) -> "GameState":
    """Apply card swapped event - swap supporting and attacking cards."""
    player = state.players[event.player_id]
    supporting_card = state.cards.get(event.supporting_card_id)
    attacking_card = state.cards.get(event.attacking_card_id)
    
    if supporting_card and attacking_card:
        # Swap in zones
        if event.supporting_card_id in player.zones[Zone.SUPPORTING].card_ids:
            player.zones[Zone.SUPPORTING].card_ids.remove(event.supporting_card_id)
        if event.attacking_card_id in player.zones[Zone.ATTACKING].card_ids:
            player.zones[Zone.ATTACKING].card_ids.remove(event.attacking_card_id)
        
        player.zones[Zone.ATTACKING].card_ids.append(event.supporting_card_id)
        player.zones[Zone.SUPPORTING].card_ids.append(event.attacking_card_id)
        
        # Update card states
        supporting_card.zone = Zone.ATTACKING
        supporting_card.swapped_this_turn = True
        supporting_card.turns_in_zone = 0
        
        attacking_card.zone = Zone.SUPPORTING
        attacking_card.swapped_this_turn = True
        attacking_card.turns_in_zone = 0
        
        # Recalculate elements (swapped cards don't contribute this turn)
        _recalculate_elements(state, event.player_id)
    
    return state


# ============================================================================
# Association & Evolution Reducers
# ============================================================================

def _apply_card_associated(state: "GameState", event: CardAssociatedEvent) -> "GameState":
    """Apply card associated event."""
    player = state.players[event.player_id]
    assoc_card = state.cards.get(event.association_card_id)
    target_card = state.cards.get(event.target_card_id)
    
    if assoc_card and target_card:
        # Remove from source zone
        if event.source_zone:
            if event.association_card_id in player.zones[event.source_zone].card_ids:
                player.zones[event.source_zone].card_ids.remove(event.association_card_id)
        
        # Mark as associated
        assoc_card.status = CardStatus.ASSOCIATED
        
        # Add to target's associations
        if event.association_card_id not in target_card.associations:
            target_card.associations.append(event.association_card_id)
        
        # Recalculate elements
        _recalculate_elements(state, event.player_id)
    
    return state


def _apply_card_evolved(state: "GameState", event: CardEvolvedEvent) -> "GameState":
    """Apply card evolved event."""
    player = state.players[event.player_id]
    base_card = state.cards.get(event.base_card_id)
    evo_card = state.cards.get(event.evolution_card_id)
    
    if base_card and evo_card:
        target_zone = base_card.zone
        
        # Remove evolution from hand
        if event.evolution_card_id in player.zones[Zone.HAND].card_ids:
            player.zones[Zone.HAND].card_ids.remove(event.evolution_card_id)
        
        # Remove base from its zone
        if target_zone in (Zone.SUPPORTING, Zone.ATTACKING):
            if event.base_card_id in player.zones[target_zone].card_ids:
                player.zones[target_zone].card_ids.remove(event.base_card_id)
        
        # Move base to graveyard
        player.zones[Zone.GRAVEYARD].card_ids.append(event.base_card_id)
        base_card.zone = Zone.GRAVEYARD
        
        # Place evolution in target zone
        player.zones[target_zone].card_ids.append(event.evolution_card_id)
        evo_card.zone = target_zone
        evo_card.turns_in_zone = 0
        
        # Transfer associations
        evo_card.associations = base_card.associations.copy()
        base_card.associations.clear()
        
        # Recalculate elements
        _recalculate_elements(state, event.player_id)
    
    return state


# ============================================================================
# Combat Reducers
# ============================================================================

def _apply_attack_declared(state: "GameState", event: AttackDeclaredEvent) -> "GameState":
    """Apply attack declared event - mark attacker as having attacked."""
    attacker = state.cards.get(event.attacker_id)
    
    if attacker:
        attacker.has_attacked_this_turn = True
    
    return state


def _apply_damage_dealt(state: "GameState", event: DamageDealtEvent) -> "GameState":
    """Apply damage dealt event - reduce target's health."""
    target = state.cards.get(event.target_id)
    
    if target and event.final_damage > 0:
        target.current_health -= event.final_damage
    
    return state


def _apply_card_destroyed(state: "GameState", event: CardDestroyedEvent) -> "GameState":
    """Apply card destroyed event - move to graveyard."""
    player = state.players[event.owner_id]
    card = state.cards.get(event.card_id)
    
    if card:
        current_zone = card.zone
        
        # Remove from current zone
        if current_zone in (Zone.SUPPORTING, Zone.ATTACKING):
            if event.card_id in player.zones[current_zone].card_ids:
                player.zones[current_zone].card_ids.remove(event.card_id)
        
        # Add to graveyard
        if event.card_id not in player.zones[Zone.GRAVEYARD].card_ids:
            player.zones[Zone.GRAVEYARD].card_ids.append(event.card_id)
        
        card.zone = Zone.GRAVEYARD
        
        # Recalculate elements
        _recalculate_elements(state, event.owner_id)
    
    return state


# ============================================================================
# Element Reducers
# ============================================================================

def _apply_elements_consumed(state: "GameState", event: ElementsConsumedEvent) -> "GameState":
    """Apply elements consumed event - reduce element pool."""
    player = state.players[event.player_id]
    
    for element_id, amount in event.elements.items():
        current = player.element_pool.elements.get(element_id, 0)
        player.element_pool.elements[element_id] = max(0, current - amount)
    
    return state


def _apply_elements_restored(state: "GameState", event: ElementsRestoredEvent) -> "GameState":
    """Apply elements restored event - restore element pool."""
    player = state.players[event.player_id]
    
    player.element_pool.elements = dict(event.elements)
    
    return state


# ============================================================================
# Turn & Phase Reducers
# ============================================================================

def _apply_turn_started(state: "GameState", event: TurnStartedEvent) -> "GameState":
    """Apply turn started event."""
    state.active_player_id = event.player_id
    state.turn_number = event.turn_number
    
    player = state.players[event.player_id]
    player.has_passed_phase = False
    
    # Reset card turn flags
    for card_id in player.get_active_cards():
        card = state.cards.get(card_id)
        if card:
            card.has_attacked_this_turn = False
            card.swapped_this_turn = False
            if card.status == CardStatus.SWAPPED:
                card.status = CardStatus.READY
    
    return state


def _apply_turn_ended(state: "GameState", event: TurnEndedEvent) -> "GameState":
    """Apply turn ended event."""
    player = state.players[event.player_id]
    
    # Increment turns in zone for all active cards
    for card_id in player.get_active_cards():
        card = state.cards.get(card_id)
        if card:
            card.turns_in_zone += 1
    
    # Increment player turn count
    player.turn_count += 1
    
    return state


def _apply_phase_changed(state: "GameState", event: PhaseChangedEvent) -> "GameState":
    """Apply phase changed event."""
    if event.to_phase:
        state.current_phase = event.to_phase
    
    return state


# ============================================================================
# Game-Level Reducers
# ============================================================================

def _apply_game_started(state: "GameState", event: GameStartedEvent) -> "GameState":
    """Apply game started event."""
    state.status = GameStatus.IN_PROGRESS
    state.active_player_id = event.first_player_id
    
    return state


def _apply_game_ended(state: "GameState", event: GameEndedEvent) -> "GameState":
    """Apply game ended event."""
    state.status = GameStatus.FINISHED
    state.winner_id = event.winner_id
    
    return state


def _apply_no_defender(state: "GameState", event: NoDefenderEvent) -> "GameState":
    """Apply no defender event."""
    if event.must_defend:
        state.status = GameStatus.PAUSED
        state.pending_action = "force_defend"
    elif event.game_lost:
        state.status = GameStatus.FINISHED
        # Winner is the attacker
        state.winner_id = event.attacker_id
    
    return state


# ============================================================================
# Helper Functions
# ============================================================================

def _recalculate_elements(state: "GameState", player_id: str) -> None:
    """
    Recalculate element pool for a player based on their active cards.
    
    Note: This mutates the state in place (called from within reducers
    that already have a copy).
    """
    player = state.players[player_id]
    player.element_pool.elements.clear()
    player.element_pool.max_elements.clear()
    
    for card_id in player.get_active_cards():
        card = state.cards.get(card_id)
        if card and card.zone in (Zone.SUPPORTING, Zone.ATTACKING):
            # Swapped cards don't contribute this turn
            if card.swapped_this_turn:
                continue
            # Associated cards don't contribute
            if card.status == CardStatus.ASSOCIATED:
                continue
            
            for contrib in card.element_contribution:
                current = player.element_pool.elements.get(contrib.element_id, 0)
                player.element_pool.elements[contrib.element_id] = current + contrib.amount
    
    player.element_pool.max_elements = dict(player.element_pool.elements)

