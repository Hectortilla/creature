"""
Game Reducer

Functions that apply events to game state via in-place mutation.
The reducer is the ONLY place where state mutations happen.

Pipeline:
    apply_event(state, players, event)  →  mutates state & players in place
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from app.models.game.attack import PendingAttack
from app.models.game.card import ActiveStatus
from app.models.game.enums import CardStatus, GameStatus, Zone
from app.models.game.events import (
    AttackDeclaredEvent,
    AttackResolvedEvent,
    CardAssociatedEvent,
    CardDestroyedEvent,
    CardDrawnEvent,
    CardEvolvedEvent,
    CardExiledEvent,
    CardHealthChangedEvent,
    CardPlayedEvent,
    CardPromotedEvent,
    CardRevivedEvent,
    CardSwappedEvent,
    DamageDealtEvent,
    ElementsConsumedEvent,
    ElementsRestoredEvent,
    ForcedSwapRequestedEvent,
    GameEndedEvent,
    GameEvent,
    GameStartedEvent,
    HealingAppliedEvent,
    NoDefenderEvent,
    PhaseChangedEvent,
    StatusAppliedEvent,
    StatusExpiredEvent,
    StatusTickedEvent,
    TurnEndedEvent,
    TurnStartedEvent,
)

if TYPE_CHECKING:
    from app.models.game.card import GameCard
    from app.models.game.player import PlayerState
    from app.models.game.state import GameState


# Dispatch table: event type -> handler function
_EVENT_HANDLERS: dict[type, Callable] = {}


def _handler(event_type):
    """Decorator to register an event handler."""

    def decorator(fn):
        _EVENT_HANDLERS[event_type] = fn
        return fn

    return decorator


def apply_event(
    state: GameState, players: dict[str, PlayerState], event: GameEvent
) -> tuple[GameState, dict[str, PlayerState]]:
    """
    Apply a single event to the game state and players (in place).

    Returns the same (state, players) tuple for call-site compatibility.
    """
    handler = _EVENT_HANDLERS.get(type(event))
    if handler:
        handler(state, players, event)

    state.room.players = players
    return state, players


# ── Zone mutation helpers ────────────────────────────────────────────────


def _remove_from_zone(player: PlayerState, zone: Zone, instance_id: str) -> None:
    ids = player.zones[zone.name].card_ids
    if instance_id in ids:
        ids.remove(instance_id)


def _add_to_zone(player: PlayerState, zone: Zone, instance_id: str) -> None:
    ids = player.zones[zone.name].card_ids
    if instance_id not in ids:
        ids.append(instance_id)


def _move_zone(player: PlayerState, instance_id: str, from_zone: Zone, to_zone: Zone) -> None:
    _remove_from_zone(player, from_zone, instance_id)
    _add_to_zone(player, to_zone, instance_id)


def _detach_association(state: GameState, card: GameCard) -> None:
    """Unlink a card from the host it was associated with, if any."""
    if not card.association_target_id:
        return
    host = state.cards[card.association_target_id]
    if card.instance_id in host.associations:
        host.associations.remove(card.instance_id)
    card.association_target_id = None


# ============================================================================
# Card Movement Reducers
# ============================================================================


@_handler(CardDrawnEvent)
def _apply_card_drawn(state, players, event: CardDrawnEvent) -> None:
    """Move a card from deck to hand."""
    card = state.cards[event.instance_id]
    _move_zone(players[event.player_id], event.instance_id, Zone.DECK, Zone.HAND)
    card.zone = Zone.HAND


@_handler(CardPlayedEvent)
def _apply_card_played(state, players, event: CardPlayedEvent) -> None:
    """Move a card from hand to supporting zone."""
    card = state.cards[event.instance_id]
    _move_zone(players[event.player_id], event.instance_id, Zone.HAND, Zone.SUPPORTING)
    card.zone = Zone.SUPPORTING
    card.turns_in_zone = 0
    _recalculate_elements(state, players, event.player_id)


@_handler(CardPromotedEvent)
def _apply_card_promoted(state, players, event: CardPromotedEvent) -> None:
    """Move a card from supporting to attacking zone."""
    card = state.cards[event.instance_id]
    _move_zone(players[event.player_id], event.instance_id, Zone.SUPPORTING, Zone.ATTACKING)
    card.zone = Zone.ATTACKING
    card.turns_in_zone = 0
    _recalculate_elements(state, players, event.player_id)

    # If this promotion resolves a force defend, resume normal game flow
    if state.status == GameStatus.PAUSED and state.pending_action == "force_defend":
        state.status = GameStatus.IN_PROGRESS
        state.pending_action = None
        state.pending_defender_id = None
        state.pending_attack = None


@_handler(CardSwappedEvent)
def _apply_card_swapped(state, players, event: CardSwappedEvent) -> None:
    """Swap a supporting card and an attacking card between their zones."""
    player = players[event.player_id]
    supporting_card = state.cards[event.supporting_card_id]
    attacking_card = state.cards[event.attacking_card_id]

    _move_zone(player, event.supporting_card_id, Zone.SUPPORTING, Zone.ATTACKING)
    _move_zone(player, event.attacking_card_id, Zone.ATTACKING, Zone.SUPPORTING)

    # Swapped cards don't contribute elements this turn.
    supporting_card.zone = Zone.ATTACKING
    attacking_card.zone = Zone.SUPPORTING
    for card in (supporting_card, attacking_card):
        card.swapped_this_turn = True
        card.turns_in_zone = 0

    _recalculate_elements(state, players, event.player_id)

    if state.status == GameStatus.PAUSED and state.pending_action == "forced_swap":
        state.status = GameStatus.IN_PROGRESS
        state.pending_action = None
        state.pending_defender_id = None
        state.pending_forced_swap_target_id = None
        state.pending_forced_swap_source_id = None


# ============================================================================
# Association & Evolution Reducers
# ============================================================================


@_handler(CardAssociatedEvent)
def _apply_card_associated(state, players, event: CardAssociatedEvent) -> None:
    player = players[event.player_id]
    assoc_card = state.cards[event.association_card_id]
    target_card = state.cards[event.target_card_id]

    if event.source_zone:
        _remove_from_zone(player, event.source_zone, event.association_card_id)
    assoc_card.status = CardStatus.ASSOCIATED
    assoc_card.association_target_id = target_card.instance_id
    if event.association_card_id not in target_card.associations:
        target_card.associations.append(event.association_card_id)
    _recalculate_elements(state, players, event.player_id)


@_handler(CardEvolvedEvent)
def _apply_card_evolved(state, players, event: CardEvolvedEvent) -> None:
    player = players[event.player_id]
    base_card = state.cards[event.base_card_id]
    evo_card = state.cards[event.evolution_card_id]

    target_zone = base_card.zone

    _remove_from_zone(player, Zone.HAND, event.evolution_card_id)
    if target_zone in (Zone.SUPPORTING, Zone.ATTACKING):
        _remove_from_zone(player, target_zone, event.base_card_id)

    # Base goes to the graveyard; the evolution takes its place.
    _add_to_zone(player, Zone.GRAVEYARD, event.base_card_id)
    base_card.zone = Zone.GRAVEYARD

    _add_to_zone(player, target_zone, event.evolution_card_id)
    evo_card.zone = target_zone
    evo_card.turns_in_zone = 0

    # Transfer associations from base to evolution.
    evo_card.associations = base_card.associations.copy()
    base_card.associations.clear()

    _recalculate_elements(state, players, event.player_id)


# ============================================================================
# Combat Reducers
# ============================================================================


@_handler(AttackDeclaredEvent)
def _apply_attack_declared(state, players, event: AttackDeclaredEvent) -> None:
    """Mark the attacker as having attacked and record cooldown usage."""
    attacker = state.cards[event.attacker_id]
    attacker.has_attacked_this_turn = True
    attacker.attack_last_used[event.attack_id] = state.turn_number


@_handler(AttackResolvedEvent)
def _apply_attack_resolved(state, players, event: AttackResolvedEvent) -> None:
    """Attack resolution is informational; follow-up effects react to it."""


@_handler(DamageDealtEvent)
def _apply_damage_dealt(state, players, event: DamageDealtEvent) -> None:
    target = state.cards[event.target_id]
    if event.final_damage > 0:
        target.current_health -= event.final_damage


@_handler(CardHealthChangedEvent)
def _apply_card_health_changed(state, players, event: CardHealthChangedEvent) -> None:
    """Apply non-combat health changes (DoT, effect damage, effect healing)."""
    target = state.cards[event.target_id]
    target.current_health = event.new_health if event.new_health else target.current_health + event.delta


@_handler(HealingAppliedEvent)
def _apply_healing_applied(state, players, event: HealingAppliedEvent) -> None:
    target = state.cards[event.target_id]
    target.current_health = min(target.health, event.new_health)


@_handler(StatusAppliedEvent)
def _apply_status_applied(state, players, event: StatusAppliedEvent) -> None:
    """Attach a runtime status to a card."""
    target = state.cards[event.target_id]
    target.active_statuses.append(
        ActiveStatus(
            status_type=event.status_type,
            source_card_id=event.source_card_id,
            source_atom_id=event.source_atom_id,
            remaining_turns=event.duration_turns,
            tick_on=event.tick_on,
            expires_on=event.expires_on,
            payload=dict(event.payload),
        )
    )


@_handler(StatusTickedEvent)
def _apply_status_ticked(state, players, event: StatusTickedEvent) -> None:
    """Consume one tick of a status: count down its delay first, then duration."""
    target = state.cards[event.target_id]
    for status in target.active_statuses:
        if status.status_id != event.status_id:
            continue
        if int(status.payload.get("delay_turns", 0)) > 0:
            status.payload["delay_turns"] = int(status.payload["delay_turns"]) - 1
        elif status.remaining_turns > 0:
            status.remaining_turns -= 1
        break


@_handler(StatusExpiredEvent)
def _apply_status_expired(state, players, event: StatusExpiredEvent) -> None:
    target = state.cards[event.target_id]
    target.active_statuses = [s for s in target.active_statuses if s.status_id != event.status_id]


@_handler(CardExiledEvent)
def _apply_card_exiled(state, players, event: CardExiledEvent) -> None:
    """Move a card out of all normal zones into EXILED."""
    player = players[event.owner_id]
    card = state.cards[event.instance_id]
    for zone in Zone:
        _remove_from_zone(player, zone, event.instance_id)
    _add_to_zone(player, Zone.EXILED, event.instance_id)
    card.zone = Zone.EXILED
    card.status = CardStatus.READY
    _detach_association(state, card)
    _recalculate_elements(state, players, event.owner_id)


@_handler(ForcedSwapRequestedEvent)
def _apply_forced_swap_requested(state, players, event: ForcedSwapRequestedEvent) -> None:
    state.status = GameStatus.PAUSED
    state.pending_action = "forced_swap"
    state.pending_defender_id = event.owner_id
    state.pending_forced_swap_target_id = event.target_card_id
    state.pending_forced_swap_source_id = event.source_card_id


@_handler(CardRevivedEvent)
def _apply_card_revived(state, players, event: CardRevivedEvent) -> None:
    """Swap a graveyard card back into the source card's active zone."""
    player = players[event.player_id]
    source = state.cards[event.source_card_id]
    revived = state.cards[event.revived_card_id]
    if event.revived_card_id in player.zones[Zone.GRAVEYARD.name].card_ids:
        source_zone = source.zone
        _move_zone(player, source.instance_id, source_zone, Zone.GRAVEYARD)
        source.zone = Zone.GRAVEYARD
        _move_zone(player, event.revived_card_id, Zone.GRAVEYARD, source_zone)
        revived.zone = source_zone
        revived.turns_in_zone = 0
        _recalculate_elements(state, players, event.player_id)


@_handler(CardDestroyedEvent)
def _apply_card_destroyed(state, players, event: CardDestroyedEvent) -> None:
    """Move a destroyed card to the graveyard."""
    player = players[event.owner_id]
    card = state.cards[event.instance_id]
    if card.zone in (Zone.SUPPORTING, Zone.ATTACKING):
        _remove_from_zone(player, card.zone, event.instance_id)
    _add_to_zone(player, Zone.GRAVEYARD, event.instance_id)
    card.zone = Zone.GRAVEYARD
    _detach_association(state, card)
    _recalculate_elements(state, players, event.owner_id)


# ============================================================================
# Element Reducers
# ============================================================================


@_handler(ElementsConsumedEvent)
def _apply_elements_consumed(state, players, event: ElementsConsumedEvent) -> None:
    pool = players[event.player_id].element_pool
    for element_id, amount in event.elements.items():
        pool.elements[element_id] = max(0, pool.elements.get(element_id, 0) - amount)


@_handler(ElementsRestoredEvent)
def _apply_elements_restored(state, players, event: ElementsRestoredEvent) -> None:
    players[event.player_id].element_pool.elements = dict(event.elements)


# ============================================================================
# Turn & Phase Reducers
# ============================================================================


@_handler(TurnStartedEvent)
def _apply_turn_started(state, players, event: TurnStartedEvent) -> None:
    state.active_player_id = event.player_id
    state.turn_number = event.turn_number

    player = players[event.player_id]
    player.has_passed_phase = False
    for card_id in player.get_active_cards():
        card = state.cards[card_id]
        card.has_attacked_this_turn = False
        card.swapped_this_turn = False
        if card.status == CardStatus.SWAPPED:
            card.status = CardStatus.READY


@_handler(TurnEndedEvent)
def _apply_turn_ended(state, players, event: TurnEndedEvent) -> None:
    player = players[event.player_id]
    for card_id in player.get_active_cards():
        card = state.cards[card_id]
        card.turns_in_zone += 1
    player.turn_count += 1


@_handler(PhaseChangedEvent)
def _apply_phase_changed(state, players, event: PhaseChangedEvent) -> None:
    if event.to_phase:
        state.current_phase = event.to_phase


# ============================================================================
# Game-Level Reducers
# ============================================================================


@_handler(GameStartedEvent)
def _apply_game_started(state, players, event: GameStartedEvent) -> None:
    state.status = GameStatus.IN_PROGRESS
    state.active_player_id = event.first_player_id


@_handler(GameEndedEvent)
def _apply_game_ended(state, players, event: GameEndedEvent) -> None:
    state.status = GameStatus.FINISHED
    state.winner_id = event.winner_id


@_handler(NoDefenderEvent)
def _apply_no_defender(state, players, event: NoDefenderEvent) -> None:
    if event.must_defend:
        state.status = GameStatus.PAUSED
        state.pending_action = "force_defend"
        state.pending_defender_id = event.defender_id
        state.pending_attack = PendingAttack(
            attacker_id=event.pending_attacker_card_id,
            attack_id=event.pending_attack_id,
            attacker_owner_id=event.pending_attacker_owner_id,
        )
    elif event.game_lost:
        state.status = GameStatus.FINISHED
        state.winner_id = event.attacker_id  # Winner is the attacker


# ============================================================================
# Helper Functions
# ============================================================================


def _recalculate_elements(state: GameState, players: dict[str, PlayerState], player_id: str) -> None:
    """
    Recalculate a player's element pool from their active cards.

    Mutates in place. Reads from the `players` dict (not state.room.players) so
    it sees the most up-to-date zone data from the current handler. Available
    amounts are preserved across recalculation so already-consumed elements are
    not refunded.
    """
    player = players[player_id]
    old_max = dict(player.element_pool.max_elements)
    old_available = dict(player.element_pool.elements)

    # New max from current contributors (swapped/associated cards don't contribute).
    new_max: dict[int, int] = {}
    for card_id in player.get_active_cards():
        card = state.cards[card_id]
        if card.zone not in (Zone.SUPPORTING, Zone.ATTACKING):
            continue
        if card.swapped_this_turn or card.status == CardStatus.ASSOCIATED:
            continue
        for contrib in card.element_contribution:
            new_max[contrib.element_id] = new_max.get(contrib.element_id, 0) + contrib.amount

    # Carry available amounts forward: gain on max increase, cap on max decrease.
    new_available: dict[int, int] = {}
    for elem_id in set(old_max) | set(new_max) | set(old_available):
        prev_max = old_max.get(elem_id, 0)
        curr_max = new_max.get(elem_id, 0)
        prev_avail = old_available.get(elem_id, 0)
        if curr_max >= prev_max:
            new_available[elem_id] = prev_avail + (curr_max - prev_max)
        else:
            new_available[elem_id] = min(prev_avail, curr_max)

    player.element_pool.elements = {k: v for k, v in new_available.items() if v > 0}
    player.element_pool.max_elements = {k: v for k, v in new_max.items() if v > 0}
