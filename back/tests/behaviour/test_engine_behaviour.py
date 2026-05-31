"""Behaviour fixture-approval tests over the game engine.

Drives a deterministic playthrough (fixed RNG seed, no DB) and snapshots the
resulting action/event transcript with syrupy. Any change to the rules, reducer,
or effects that alters engine behaviour surfaces as a snapshot diff to review and
deliberately approve — a golden-file safety net for the crown-jewel engine.

Regenerate intentionally after an *intended* behaviour change:

    uv run pytest tests/behaviour --snapshot-update
"""

from __future__ import annotations

import random
from typing import Any

import pytest

# Reuse the deterministic two-player builder + client-payload helpers that the
# engine smoke test already maintains, so both suites drive the engine identically.
from tests.unit.test_engine_smoke import _act_player_id, _build_game, _client_payload

pytestmark = pytest.mark.unit


def _event_types(result: Any) -> list[str]:
    """Sorted, de-duplicated event class names — the deterministic part of a step.

    (Full event payloads carry per-run uuids, so we fingerprint by type.)
    """
    return sorted({type(e).__name__ for e in (result.events or [])})


def _playthrough(steps: int = 80) -> list[dict[str, Any]]:
    """Run a fixed-seed game and capture a deterministic transcript."""
    random.seed(1234)
    engine, state = _build_game()

    result = engine.start_game(state)
    assert result.success, result.error
    state = result.state
    transcript: list[dict[str, Any]] = [{"step": 0, "action": "start_game", "events": _event_types(result)}]

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
