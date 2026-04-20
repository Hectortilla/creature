"""
Game Engine

Stateless coordinator that orchestrates the game pipeline:
    Action → Validator → action.to_events() → EventLoop → Reducer → New State
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Optional, TYPE_CHECKING
import traceback

if TYPE_CHECKING:
    from app.models.game.player import PlayerState
    from app.websocket.models import GameRoom

from app.models.game.enums import Zone, TurnPhase, GameStatus
from app.models.game.state import GameState, GameConfiguration
from app.models.game.events import (
    GameEvent,
    GameStartedEvent,
    GameEndedEvent,
    TurnStartedEvent,
    PhaseChangedEvent,
)
from app.game.actions import (
    Action,
    DrawAction,
    PassPhaseAction,
    ConcedeAction,
    ForceDefendAction,
    ACTION_TYPES,
    create_action,
)
from app.game.validators import RuleValidator
from app.game.event_loop import EventLoop
from app.game.reducer import apply_event


@dataclass
class ActionResult:
    success: bool
    events: list[GameEvent] = field(default_factory=list)
    error: Optional[str] = None
    game_over: bool = False
    winner_id: Optional[str] = None
    state: Optional[GameState] = None
    final_players: Optional[dict[str, "PlayerState"]] = None
    valid_actions: list[dict[str, Any]] = field(default_factory=list)


class GameEngine:
    """Stateless engine — coordinates validation, event generation, and state updates."""

    def __init__(self, config: Optional[GameConfiguration] = None):
        self.config = config or GameConfiguration()
        self.validator = RuleValidator()
        self.event_loop = EventLoop()

    def create_game(self, room: "GameRoom") -> GameState:
        state = GameState.create(room, self.config)
        for player in room.players.values():
            state._setup_deck(player)
            player.shuffle_deck()
        state.status = GameStatus.STARTING
        return state

    def start_game(self, state: "GameRoom") -> ActionResult:
        player_ids = list(state.room.players.keys())
        first_player_id = random.choice(player_ids)

        initial_events: list[GameEvent] = [
            GameStartedEvent(game_id=state.game_id, player_ids=player_ids, first_player_id=first_player_id),
            TurnStartedEvent(game_id=state.game_id, player_id=first_player_id, turn_number=1, is_first_turn=True),
        ]

        # Draw initial cards
        draw_action = DrawAction(player_id=first_player_id, count=self.config.initial_draw)
        initial_events.extend(draw_action.to_events(state))

        initial_events.append(PhaseChangedEvent(
            game_id=state.game_id, player_id=first_player_id,
            from_phase=TurnPhase.DRAW, to_phase=TurnPhase.PLACEMENT,
        ))

        result = self.event_loop.process(state, state.room.players, initial_events)
        if result.final_state:
            result.final_state.room.players = result.final_players

        valid_actions = self.get_valid_actions(result.final_state) if result.final_state else []

        # Auto-advance through phases with no phase-specific actions
        if result.final_state and valid_actions:
            final_state, all_events, valid_actions, game_over, winner_id = self._auto_advance_phases(
                result.final_state, result.all_events, valid_actions,
            )
        else:
            final_state = result.final_state
            all_events = result.all_events

        return ActionResult(
            success=True, events=all_events,
            state=final_state, final_players=final_state.room.players if final_state else result.final_players,
            valid_actions=valid_actions,
        )

    def process_action(self, state: GameState, action: Action) -> ActionResult:
        # 1. Validate
        validation = self.validator.validate(state, action)
        if not validation.valid:
            return ActionResult(success=False, error=validation.error, state=state)

        try:
            # 2. Generate events (action knows how)
            events = action.to_events(state)

            # 3. Process through event loop (reducer + effect triggers)
            result = self.event_loop.process(state, state.room.players, events)
            result.final_state.room.players = result.final_players

            # 4. Check game end
            winner_id = result.final_state.check_game_end()
            game_over = winner_id is not None

            if game_over and result.final_state.status != GameStatus.FINISHED:
                loser_id = next((pid for pid in result.final_players if pid != winner_id), None)
                if loser_id:
                    end_event = GameEndedEvent(
                        game_id=result.final_state.game_id,
                        winner_id=winner_id, loser_id=loser_id,
                        reason="No cards remaining",
                    )
                    result.final_state, result.final_players = apply_event(result.final_state, result.final_players, end_event)
                    result.final_state.room.players = result.final_players
                    result.all_events.append(end_event)

            valid_actions = self.get_valid_actions(result.final_state) if result.final_state and not game_over else []

            # Auto-advance through phases with no phase-specific actions
            final_state = result.final_state
            all_events = result.all_events
            if final_state and not game_over and valid_actions:
                final_state, all_events, valid_actions, game_over, winner_id = self._auto_advance_phases(
                    final_state, all_events, valid_actions,
                )

            return ActionResult(
                success=True, events=all_events,
                game_over=game_over or final_state.status == GameStatus.FINISHED,
                winner_id=final_state.winner_id,
                state=final_state, final_players=final_state.room.players,
                valid_actions=valid_actions,
            )
        except Exception:
            return ActionResult(success=False, error=traceback.format_exc(), state=state)

    def process_action_from_dict(self, state: GameState, player_id: str, action_data: dict) -> ActionResult:
        if player_id not in state.room.players:
            return ActionResult(success=False, error="Player not in this game", state=state)
        action_type = action_data.get("action_type")
        if not action_type:
            return ActionResult(success=False, error="Missing action_type", state=state)
        try:
            action_params = {k: v for k, v in action_data.items() if k != "action_type"}
            action = create_action(action_type, player_id=player_id, **action_params)
            return self.process_action(state, action)
        except Exception as e:
            return ActionResult(success=False, error=str(e), state=state)

    def _only_pass_and_concede(self, valid_actions: list[dict[str, Any]]) -> bool:
        """Check if valid_actions contains only pass and concede (no phase-specific actions)."""
        return all(a.get("action_type") in ("pass", "concede") for a in valid_actions)

    def _auto_advance_phases(
        self,
        state: GameState,
        accumulated_events: list[GameEvent],
        valid_actions: list[dict[str, Any]],
    ) -> tuple[GameState, list[GameEvent], list[dict[str, Any]], bool, Optional[str]]:
        """
        Auto-advance through phases that have no phase-specific actions.

        After any action, if the only remaining valid actions are pass and concede,
        automatically process a PassPhaseAction to advance to the next meaningful phase.
        """
        game_over = state.winner_id is not None
        winner_id = state.winner_id
        iterations = 0
        max_iterations = 14  # 7 phases × 2 players

        while (
            iterations < max_iterations
            and not game_over
            and state.status == GameStatus.IN_PROGRESS
            and valid_actions
            and self._only_pass_and_concede(valid_actions)
        ):
            iterations += 1

            pass_action = PassPhaseAction(player_id=state.active_player_id)

            validation = self.validator.validate(state, pass_action)
            if not validation.valid:
                break

            events = pass_action.to_events(state)
            result = self.event_loop.process(state, state.room.players, events)
            result.final_state.room.players = result.final_players
            state = result.final_state
            accumulated_events.extend(result.all_events)

            winner_id = state.check_game_end()
            game_over = winner_id is not None

            if game_over and state.status != GameStatus.FINISHED:
                loser_id = next((pid for pid in result.final_players if pid != winner_id), None)
                if loser_id:
                    end_event = GameEndedEvent(
                        game_id=state.game_id,
                        winner_id=winner_id, loser_id=loser_id,
                        reason="No cards remaining",
                    )
                    state, final_players = apply_event(state, result.final_players, end_event)
                    state.room.players = final_players
                    accumulated_events.append(end_event)

            if not game_over:
                valid_actions = self.get_valid_actions(state)

        return state, accumulated_events, valid_actions, game_over, winner_id

    def get_valid_actions(self, state: GameState) -> list[dict[str, Any]]:
        actions: list[Action] = []

        # Pass + Concede always available
        actions.append(PassPhaseAction(player_id=state.active_player_id))
        actions.append(ConcedeAction(player_id=state.active_player_id))

        # Force defend: defender picks a supporting card
        if state.status == GameStatus.PAUSED and state.pending_action == "force_defend":
            if state.pending_defender_id:
                actions.extend(ForceDefendAction.get_valid(state, state.pending_defender_id))
            return [a.to_dict(state) for a in actions]

        # Enumerate valid actions for current phase from each action type
        for action_cls in ACTION_TYPES.values():
            phases = action_cls.model_fields["valid_phases"].default
            if phases and state.current_phase in phases:
                actions.extend(action_cls.get_valid(state, state.active_player_id))

        return [a.to_dict(state) for a in actions]


# Singleton
_engine: Optional[GameEngine] = None

def get_engine(config: Optional[GameConfiguration] = None) -> GameEngine:
    global _engine
    if _engine is None:
        _engine = GameEngine(config)
    return _engine
