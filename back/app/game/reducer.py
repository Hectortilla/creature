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


def apply_event(state: "GameState", players: dict[str, "PlayerState"], event: GameEvent) -> tuple["GameState", dict[str, "PlayerState"]]:
    """
    Apply a single event to the game state and players.
    
    This is the main entry point for the reducer.
    Returns a new state and players dict with the event applied.
    
    Args:
        state: Current game state (not modified)
        players: Current players dict (not modified) - kept for compatibility
        event: Event to apply
    
    Returns:
        Tuple of (new game state, new players dict) with event applied
    """
    from app.models.game.player import PlayerState
    
    # Create deep copies to ensure immutability
    # Note: We use a custom approach to handle the room reference
    # We deep copy state but need to preserve the room reference
    import copy
    new_state = copy.deepcopy(state)
    # Restore room reference (don't deep copy it to avoid circular issues)
    new_state.room = state.room
    new_players = {pid: deepcopy(player) for pid, player in players.items()}
    
    # Helper to update room.players after reducer call
    def update_and_return(result_state, result_players):
        result_state.room.players = result_players
        return result_state, result_players
    
    # Dispatch to specific handler
    if isinstance(event, CardDrawnEvent):
        return update_and_return(*_apply_card_drawn(new_state, new_players, event))
    elif isinstance(event, CardMovedEvent):
        return update_and_return(*_apply_card_moved(new_state, new_players, event))
    elif isinstance(event, CardPlayedEvent):
        return update_and_return(*_apply_card_played(new_state, new_players, event))
    elif isinstance(event, CardPromotedEvent):
        return update_and_return(*_apply_card_promoted(new_state, new_players, event))
    elif isinstance(event, CardSwappedEvent):
        return update_and_return(*_apply_card_swapped(new_state, new_players, event))
    elif isinstance(event, CardAssociatedEvent):
        return update_and_return(*_apply_card_associated(new_state, new_players, event))
    elif isinstance(event, CardEvolvedEvent):
        return update_and_return(*_apply_card_evolved(new_state, new_players, event))
    elif isinstance(event, DamageDealtEvent):
        return update_and_return(*_apply_damage_dealt(new_state, new_players, event))
    elif isinstance(event, CardDestroyedEvent):
        return update_and_return(*_apply_card_destroyed(new_state, new_players, event))
    elif isinstance(event, ElementsConsumedEvent):
        return update_and_return(*_apply_elements_consumed(new_state, new_players, event))
    elif isinstance(event, ElementsRestoredEvent):
        return update_and_return(*_apply_elements_restored(new_state, new_players, event))
    elif isinstance(event, TurnStartedEvent):
        return update_and_return(*_apply_turn_started(new_state, new_players, event))
    elif isinstance(event, TurnEndedEvent):
        return update_and_return(*_apply_turn_ended(new_state, new_players, event))
    elif isinstance(event, PhaseChangedEvent):
        return update_and_return(*_apply_phase_changed(new_state, new_players, event))
    elif isinstance(event, GameStartedEvent):
        return update_and_return(*_apply_game_started(new_state, new_players, event))
    elif isinstance(event, GameEndedEvent):
        return update_and_return(*_apply_game_ended(new_state, new_players, event))
    elif isinstance(event, NoDefenderEvent):
        return update_and_return(*_apply_no_defender(new_state, new_players, event))
    elif isinstance(event, AttackDeclaredEvent):
        return update_and_return(*_apply_attack_declared(new_state, new_players, event))
    
    # Unknown event type - return state and players unchanged
    new_state.room.players = new_players
    return new_state, new_players


def apply_events(state: "GameState", players: dict[str, "PlayerState"], events: list[GameEvent]) -> tuple["GameState", dict[str, "PlayerState"]]:
    """
    Apply multiple events in sequence.
    
    Args:
        state: Initial game state
        players: Initial players dict
        events: List of events to apply in order
    
    Returns:
        Tuple of (final game state, final players dict) after all events applied
    """
    current_state = state
    current_players = players
    for event in events:
        current_state, current_players = apply_event(current_state, current_players, event)
    return current_state, current_players


# ============================================================================
# Card Movement Reducers
# ============================================================================

def _apply_card_drawn(state: "GameState", players: dict[str, "PlayerState"], event: CardDrawnEvent) -> tuple["GameState", dict[str, "PlayerState"]]:
    """Apply card drawn event - move card from deck to hand."""
    player = players[event.player_id]
    card = state.cards.get(event.card_id)
    
    if card:
        # Remove from deck
        if event.card_id in player.zones[Zone.DECK.name].card_ids:
            player.zones[Zone.DECK.name].card_ids.remove(event.card_id)
        
        # Add to hand
        if event.card_id not in player.zones[Zone.HAND.name].card_ids:
            player.zones[Zone.HAND.name].card_ids.append(event.card_id)
        
        # Update card zone
        card.zone = Zone.HAND
    
    return state, players, players


def _apply_card_moved(state: "GameState", players: dict[str, "PlayerState"], event: CardMovedEvent) -> tuple["GameState", dict[str, "PlayerState"]]:
    """Apply generic card movement event."""
    player = players[event.owner_id]
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
    
    return state, players


def _apply_card_played(state: "GameState", players: dict[str, "PlayerState"], event: CardPlayedEvent) -> tuple["GameState", dict[str, "PlayerState"]]:
    """Apply card played event - move from hand to supporting zone."""
    player = players[event.player_id]
    card = state.cards.get(event.card_id)
    
    if card:
        # Remove from hand
        if event.card_id in player.zones[Zone.HAND.name].card_ids:
            player.zones[Zone.HAND.name].card_ids.remove(event.card_id)
        
        # Add to supporting zone
        if event.card_id not in player.zones[Zone.SUPPORTING.name].card_ids:
            player.zones[Zone.SUPPORTING.name].card_ids.append(event.card_id)
        
        # Update card state
        card.zone = Zone.SUPPORTING
        card.turns_in_zone = 0
        
        # Recalculate elements
        _recalculate_elements(state, event.player_id)
    
    return state, players


def _apply_card_promoted(state: "GameState", players: dict[str, "PlayerState"], event: CardPromotedEvent) -> tuple["GameState", dict[str, "PlayerState"]]:
    """Apply card promoted event - move from supporting to attacking zone."""
    player = players[event.player_id]
    card = state.cards.get(event.card_id)
    
    if card:
        # Remove from supporting
        if event.card_id in player.zones[Zone.SUPPORTING.name].card_ids:
            player.zones[Zone.SUPPORTING.name].card_ids.remove(event.card_id)
        
        # Add to attacking
        if event.card_id not in player.zones[Zone.ATTACKING.name].card_ids:
            player.zones[Zone.ATTACKING.name].card_ids.append(event.card_id)
        
        # Update card state
        card.zone = Zone.ATTACKING
        card.turns_in_zone = 0
        
        # Recalculate elements
        _recalculate_elements(state, event.player_id)
    
    return state, players


def _apply_card_swapped(state: "GameState", players: dict[str, "PlayerState"], event: CardSwappedEvent) -> tuple["GameState", dict[str, "PlayerState"]]:
    """Apply card swapped event - swap supporting and attacking cards."""
    player = players[event.player_id]
    supporting_card = state.cards.get(event.supporting_card_id)
    attacking_card = state.cards.get(event.attacking_card_id)
    
    if supporting_card and attacking_card:
        # Swap in zones
        if event.supporting_card_id in player.zones[Zone.SUPPORTING.name].card_ids:
            player.zones[Zone.SUPPORTING.name].card_ids.remove(event.supporting_card_id)
        if event.attacking_card_id in player.zones[Zone.ATTACKING.name].card_ids:
            player.zones[Zone.ATTACKING.name].card_ids.remove(event.attacking_card_id)
        
        player.zones[Zone.ATTACKING.name].card_ids.append(event.supporting_card_id)
        player.zones[Zone.SUPPORTING.name].card_ids.append(event.attacking_card_id)
        
        # Update card states
        supporting_card.zone = Zone.ATTACKING
        supporting_card.swapped_this_turn = True
        supporting_card.turns_in_zone = 0
        
        attacking_card.zone = Zone.SUPPORTING
        attacking_card.swapped_this_turn = True
        attacking_card.turns_in_zone = 0
        
        # Recalculate elements (swapped cards don't contribute this turn)
        _recalculate_elements(state, event.player_id)
    
    return state, players


# ============================================================================
# Association & Evolution Reducers
# ============================================================================

def _apply_card_associated(state: "GameState", players: dict[str, "PlayerState"], event: CardAssociatedEvent) -> tuple["GameState", dict[str, "PlayerState"]]:
    """Apply card associated event."""
    player = players[event.player_id]
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
    
    return state, players


def _apply_card_evolved(state: "GameState", players: dict[str, "PlayerState"], event: CardEvolvedEvent) -> tuple["GameState", dict[str, "PlayerState"]]:
    """Apply card evolved event."""
    player = players[event.player_id]
    base_card = state.cards.get(event.base_card_id)
    evo_card = state.cards.get(event.evolution_card_id)
    
    if base_card and evo_card:
        target_zone = base_card.zone
        
        # Remove evolution from hand
        if event.evolution_card_id in player.zones[Zone.HAND.name].card_ids:
            player.zones[Zone.HAND.name].card_ids.remove(event.evolution_card_id)
        
        # Remove base from its zone
        if target_zone in (Zone.SUPPORTING, Zone.ATTACKING):
            if event.base_card_id in player.zones[target_zone].card_ids:
                player.zones[target_zone].card_ids.remove(event.base_card_id)
        
        # Move base to graveyard
        player.zones[Zone.GRAVEYARD.name].card_ids.append(event.base_card_id)
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
    
    return state, players


# ============================================================================
# Combat Reducers
# ============================================================================

def _apply_attack_declared(state: "GameState", players: dict[str, "PlayerState"], event: AttackDeclaredEvent) -> tuple["GameState", dict[str, "PlayerState"]]:
    """Apply attack declared event - mark attacker as having attacked."""
    attacker = state.cards.get(event.attacker_id)
    
    if attacker:
        attacker.has_attacked_this_turn = True
    
    return state, players


def _apply_damage_dealt(state: "GameState", players: dict[str, "PlayerState"], event: DamageDealtEvent) -> tuple["GameState", dict[str, "PlayerState"]]:
    """Apply damage dealt event - reduce target's health."""
    target = state.cards.get(event.target_id)
    
    if target and event.final_damage > 0:
        target.current_health -= event.final_damage
    
    return state, players


def _apply_card_destroyed(state: "GameState", players: dict[str, "PlayerState"], event: CardDestroyedEvent) -> tuple["GameState", dict[str, "PlayerState"]]:
    """Apply card destroyed event - move to graveyard."""
    player = players[event.owner_id]
    card = state.cards.get(event.card_id)
    
    if card:
        current_zone = card.zone
        
        # Remove from current zone
        if current_zone in (Zone.SUPPORTING, Zone.ATTACKING):
            if event.card_id in player.zones[current_zone].card_ids:
                player.zones[current_zone].card_ids.remove(event.card_id)
        
        # Add to graveyard
        if event.card_id not in player.zones[Zone.GRAVEYARD.name].card_ids:
            player.zones[Zone.GRAVEYARD.name].card_ids.append(event.card_id)
        
        card.zone = Zone.GRAVEYARD
        
        # Recalculate elements
        _recalculate_elements(state, event.owner_id)
    
    return state, players


# ============================================================================
# Element Reducers
# ============================================================================

def _apply_elements_consumed(state: "GameState", players: dict[str, "PlayerState"], event: ElementsConsumedEvent) -> tuple["GameState", dict[str, "PlayerState"]]:
    """Apply elements consumed event - reduce element pool."""
    player = players[event.player_id]
    
    for element_id, amount in event.elements.items():
        current = player.element_pool.elements.get(element_id, 0)
        player.element_pool.elements[element_id] = max(0, current - amount)
    
    return state, players


def _apply_elements_restored(state: "GameState", players: dict[str, "PlayerState"], event: ElementsRestoredEvent) -> tuple["GameState", dict[str, "PlayerState"]]:
    """Apply elements restored event - restore element pool."""
    player = players[event.player_id]
    
    player.element_pool.elements = dict(event.elements)
    
    return state, players


# ============================================================================
# Turn & Phase Reducers
# ============================================================================

def _apply_turn_started(state: "GameState", players: dict[str, "PlayerState"], event: TurnStartedEvent) -> tuple["GameState", dict[str, "PlayerState"]]:
    """Apply turn started event."""
    state.active_player_id = event.player_id
    state.turn_number = event.turn_number
    
    player = players[event.player_id]
    player.has_passed_phase = False
    
    # Reset card turn flags
    for card_id in player.get_active_cards():
        card = state.cards.get(card_id)
        if card:
            card.has_attacked_this_turn = False
            card.swapped_this_turn = False
            if card.status == CardStatus.SWAPPED:
                card.status = CardStatus.READY
    
    return state, players


def _apply_turn_ended(state: "GameState", players: dict[str, "PlayerState"], event: TurnEndedEvent) -> tuple["GameState", dict[str, "PlayerState"]]:
    """Apply turn ended event."""
    player = players[event.player_id]
    
    # Increment turns in zone for all active cards
    for card_id in player.get_active_cards():
        card = state.cards.get(card_id)
        if card:
            card.turns_in_zone += 1
    
    # Increment player turn count
    player.turn_count += 1
    
    return state, players


def _apply_phase_changed(state: "GameState", players: dict[str, "PlayerState"], event: PhaseChangedEvent) -> tuple["GameState", dict[str, "PlayerState"]]:
    """Apply phase changed event."""
    if event.to_phase:
        state.current_phase = event.to_phase
    
    return state, players


# ============================================================================
# Game-Level Reducers
# ============================================================================

def _apply_game_started(state: "GameState", players: dict[str, "PlayerState"], event: GameStartedEvent) -> tuple["GameState", dict[str, "PlayerState"]]:
    """Apply game started event."""
    state.status = GameStatus.IN_PROGRESS
    state.active_player_id = event.first_player_id
    
    return state, players


def _apply_game_ended(state: "GameState", players: dict[str, "PlayerState"], event: GameEndedEvent) -> tuple["GameState", dict[str, "PlayerState"]]:
    """Apply game ended event."""
    state.status = GameStatus.FINISHED
    state.winner_id = event.winner_id
    
    return state, players


def _apply_no_defender(state: "GameState", players: dict[str, "PlayerState"], event: NoDefenderEvent) -> tuple["GameState", dict[str, "PlayerState"]]:
    """Apply no defender event."""
    if event.must_defend:
        state.status = GameStatus.PAUSED
        state.pending_action = "force_defend"
    elif event.game_lost:
        state.status = GameStatus.FINISHED
        # Winner is the attacker
        state.winner_id = event.attacker_id
    
    return state, players


# ============================================================================
# Helper Functions
# ============================================================================

def _recalculate_elements(state: "GameState", player_id: str) -> None:
    """
    Recalculate element pool for a player based on their active cards.
    
    Note: This mutates the state in place (called from within reducers
    that already have a copy).
    """
    player = players[player_id]
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

