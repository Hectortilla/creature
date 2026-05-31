"""
Turn-flow actions (Draw, Pass, Concede) and phase-skip helpers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.game.actions.base import Action
from app.models.game.enums import CardStatus, TurnPhase, Zone
from app.models.game.events import (
    CardDrawnEvent,
    ElementsRestoredEvent,
    GameEndedEvent,
    GameEvent,
    PhaseChangedEvent,
    TurnEndedEvent,
    TurnStartedEvent,
)

if TYPE_CHECKING:
    from app.game.validators import ValidationResult
    from app.models.game.state import GameState


# ── Draw ────────────────────────────────────────────────────────────────


class DrawAction(Action):
    action_type: str = "draw"
    valid_phases: list[TurnPhase] | None = [TurnPhase.DRAW]
    count: int = 1

    def validate(self, state: GameState) -> ValidationResult:
        from app.game.validators import ValidationResult

        player = state.room.get_player(self.player_id)
        deck = player.zones[Zone.DECK.name]
        if len(deck.card_ids) < self.count:
            return ValidationResult(
                valid=False,
                error=f"Not enough cards in deck (have {len(deck.card_ids)}, need {self.count})",
                error_code="NOT_ENOUGH_CARDS",
            )
        return ValidationResult(valid=True)

    def to_events(self, state: GameState) -> list[GameEvent]:
        return _draw_events(state, self.player_id, state.room.get_player(self.player_id), self.count)


# ── Pass Phase ──────────────────────────────────────────────────────────


class PassPhaseAction(Action):
    action_type: str = "pass"
    valid_phases: list[TurnPhase] | None = None

    def to_events(self, state: GameState) -> list[GameEvent]:
        events: list[GameEvent] = []
        current_phase = state.current_phase
        player = state.room.get_player(self.player_id)

        next_phase = current_phase.next_phase()
        while next_phase and _should_skip_phase(state, next_phase, self.player_id):
            next_phase = next_phase.next_phase()

        if next_phase:
            events.append(
                PhaseChangedEvent(
                    game_id=state.game_id,
                    player_id=self.player_id,
                    from_phase=current_phase,
                    to_phase=next_phase,
                )
            )
            if next_phase == TurnPhase.DRAW:
                events.extend(_draw_events(state, self.player_id, player))
        else:
            next_player_id = _get_next_player(state, self.player_id)
            next_player = state.room.get_player(next_player_id)
            events.append(
                TurnEndedEvent(game_id=state.game_id, player_id=self.player_id, turn_number=state.turn_number)
            )
            events.append(
                ElementsRestoredEvent(
                    game_id=state.game_id,
                    player_id=next_player_id,
                    elements=dict(next_player.element_pool.max_elements),
                )
            )
            events.append(
                TurnStartedEvent(
                    game_id=state.game_id,
                    player_id=next_player_id,
                    turn_number=state.turn_number + 1,
                    is_first_turn=next_player.turn_count == 0,
                )
            )
            events.extend(_draw_events(state, next_player_id, next_player))
            events.append(
                PhaseChangedEvent(
                    game_id=state.game_id,
                    player_id=next_player_id,
                    from_phase=TurnPhase.DRAW,
                    to_phase=TurnPhase.PLACEMENT,
                )
            )

        return events


# ── Concede ─────────────────────────────────────────────────────────────


class ConcedeAction(Action):
    action_type: str = "concede"
    valid_phases: list[TurnPhase] | None = None

    def to_events(self, state: GameState) -> list[GameEvent]:
        opponent = state.room.get_opponent(self.player_id)
        return [
            GameEndedEvent(
                game_id=state.game_id,
                winner_id=opponent.player_id,
                loser_id=self.player_id,
                reason="Player conceded",
            )
        ]


# ── Helpers ─────────────────────────────────────────────────────────────


def _draw_events(state: GameState, player_id: str, player, count: int | None = None) -> list[GameEvent]:
    if count is None:
        count = state.config.initial_draw if player.turn_count == 0 else state.config.normal_draw
    deck = player.zones[Zone.DECK.name]
    events: list[GameEvent] = []
    for i in range(min(count, len(deck.card_ids))):
        instance_id = deck.card_ids[i]
        card = state.get_card(instance_id)
        events.append(
            CardDrawnEvent(
                game_id=state.game_id,
                player_id=player_id,
                instance_id=instance_id,
                card_id=card.card_id if card else 0,
                cards_remaining=len(deck.card_ids) - i - 1,
            )
        )
    return events


def _should_skip_phase(state: GameState, phase: TurnPhase, player_id: str) -> bool:
    player = state.room.get_player(player_id)
    if phase == TurnPhase.PROMOTION:
        if player.zones[Zone.ATTACKING.name].is_full:
            return True
        return not any(
            (card := state.get_card(cid)) is not None and card.can_promote
            for cid in player.zones[Zone.SUPPORTING.name].card_ids
        )
    if phase == TurnPhase.SWAP:
        return (
            len(player.zones[Zone.SUPPORTING.name].card_ids) == 0
            or len(player.zones[Zone.ATTACKING.name].card_ids) == 0
        )
    if phase == TurnPhase.ASSOCIATION:
        if state.is_first_turn(player_id):
            return True
        sources = player.zones[Zone.HAND.name].card_ids + player.zones[Zone.SUPPORTING.name].card_ids
        has_source = any(
            (c := state.get_card(cid)) and c.association_ids and c.status != CardStatus.ASSOCIATED for cid in sources
        )
        if not has_source:
            return True
        return not player.get_active_cards()
    if phase == TurnPhase.EVOLUTION:
        if state.is_first_turn(player_id) or state.is_second_turn(player_id):
            return True
        evolvable_base_ids = {
            c.card_id for cid in player.get_active_cards() if (c := state.get_card(cid)) and c.can_evolve
        }
        return not any(
            (c := state.get_card(cid)) and c.evolves_from_id is not None and c.evolves_from_id in evolvable_base_ids
            for cid in player.zones[Zone.HAND.name].card_ids
        )
    if phase == TurnPhase.ATTACK:
        if state.is_first_turn(player_id):
            return True
        return not any(
            (c := state.get_card(cid)) and c.can_attack for cid in player.zones[Zone.ATTACKING.name].card_ids
        )
    return False


def _get_next_player(state: GameState, current_player_id: str) -> str:
    player_ids = list(state.room.players.keys())
    current_index = player_ids.index(current_player_id)
    return player_ids[(current_index + 1) % len(player_ids)]
