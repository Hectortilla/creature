"""Behaviour fixture-approval tests over the game engine.

Drives a deterministic playthrough (fixed RNG seed, no DB) and snapshots the
resulting action/event transcript with syrupy. Any change to the rules, reducer,
or effects that alters engine behaviour surfaces as a snapshot diff to review and
deliberately approve — a golden-file safety net for the crown-jewel engine.

Regenerate intentionally after an *intended* behaviour change:

    uv run pytest tests/behaviour --snapshot-update
"""

from __future__ import annotations

from typing import Any

import pytest

from app.models.game.enums import Zone
from app.models.game.events import GameEndedEvent

# Reuse the deterministic two-player builder + client-payload helpers that the
# engine smoke test already maintains, so both suites drive the engine identically.
from tests.unit.test_engine_smoke import _act_player_id, _build_game, _client_payload

pytestmark = pytest.mark.unit

# Load-bearing numeric payload fields: a wrong value here must fail the golden
# even though the event *type* is unchanged (the silent-correctness hole).
_NUMERIC_FIELDS = (
    "base_damage",
    "element_bonus",
    "defense_reduction",
    "final_damage",
    "remaining_health",
    "amount",
    "new_health",
    "duration_turns",
)
# Player ids ("p1"/"p2") are stable across runs; instance/card ids are per-run uuids.
_PLAYER_FIELDS = ("winner_id", "loser_id")


def _event_types(result: Any) -> list[str]:
    """Sorted, de-duplicated event class names — the deterministic part of a step.

    (Full event payloads carry per-run uuids, so we fingerprint by type.)
    """
    return sorted({type(e).__name__ for e in (result.events or [])})


def _event_numbers(result: Any) -> list[dict[str, Any]]:
    """Per-event numeric payload, uuid instance-ids stripped — pins values, not just types."""
    out: list[dict[str, Any]] = []
    for e in result.events or []:
        fields = {f: getattr(e, f) for f in _NUMERIC_FIELDS if hasattr(e, f)}
        fields.update({f: getattr(e, f) for f in _PLAYER_FIELDS if getattr(e, f, "")})
        if fields:
            out.append({"event": type(e).__name__, **fields})
    return out


def _playthrough(steps: int = 80) -> list[dict[str, Any]]:
    """Run a fixed-seed game and capture a deterministic transcript."""
    engine, state = _build_game()

    result = engine.start_game(state)
    assert result.success, result.error
    state = result.state
    transcript: list[dict[str, Any]] = [
        {"step": 0, "action": "start_game", "events": _event_types(result), "numbers": _event_numbers(result)}
    ]

    for step in range(1, steps + 1):
        if result.game_over:
            break
        valid = result.valid_actions
        assert valid, "engine produced no valid actions"
        # Prefer attacks, then any substantive action, to drive real transitions.
        chosen = next(
            (a for a in valid if a["action_type"] == "attack"),
            next((a for a in valid if a["action_type"] not in ("pass", "concede")), valid[0]),
        )
        actor = _act_player_id(state)
        result = engine.process_action_from_dict(state, actor, _client_payload(chosen))
        assert result.success, result.error
        state = result.state
        transcript.append(
            {
                "step": step,
                "actor": actor,
                "action": chosen["action_type"],
                "turn": state.turn_number,
                "phase": state.current_phase.name,
                "status": state.status.name,
                "events": _event_types(result),
                "numbers": _event_numbers(result),
            }
        )

    transcript.append(
        {
            "final": True,
            "game_over": result.game_over,
            "winner": result.winner_id,
            "turn": state.turn_number,
        }
    )
    return transcript


def test_deterministic_playthrough_transcript(snapshot: Any) -> None:
    """The fixed-seed playthrough transcript must match the approved golden file."""
    assert _playthrough() == snapshot


def test_concede_drives_game_to_terminal() -> None:
    """Conceding ends the game and awards the win to the opponent."""
    engine, state = _build_game()
    state = engine.start_game(state).state

    conceder = _act_player_id(state)
    opponent = state.room.get_opponent(conceder).player_id
    result = engine.process_action_from_dict(state, conceder, {"action_type": "concede"})

    assert result.success, result.error
    assert result.game_over
    assert result.winner_id == opponent
    ended = [e for e in result.events if isinstance(e, GameEndedEvent)]
    assert len(ended) == 1
    assert ended[0].winner_id == opponent
    assert ended[0].loser_id == conceder


def test_check_game_end_awards_win_when_board_empty() -> None:
    """A player with no cards in deck/hand/active loses; the opponent is the winner."""
    engine, state = _build_game()
    state = engine.start_game(state).state

    loser = state.room.players["p1"]
    for zone in (Zone.DECK, Zone.HAND, Zone.SUPPORTING, Zone.ATTACKING):
        loser.zones[zone.name].card_ids = []

    assert state.check_game_end() == "p2"
