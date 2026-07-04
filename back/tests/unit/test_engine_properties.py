"""Property-based structural invariants over the pure game engine.

Drives the seeded engine through Hypothesis-generated *legal* action sequences
(each choice picks among the engine's own ``valid_actions``) and asserts the
invariants that must hold after **every** action, for **any** sequence — the
class of bug that example tests never reach. Pure engine, no DB/Redis.
"""

from __future__ import annotations

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from tests.unit.test_engine_smoke import _build_game, _client_payload

pytestmark = pytest.mark.unit

_seeds = st.integers(min_value=0, max_value=2**16)
_choices = st.lists(st.integers(min_value=0, max_value=64), max_size=40)


def _iter_zone_entries(state):
    for player_id, player in state.room.players.items():
        for zone_name, zone_state in player.zones.items():
            for instance_id in zone_state.card_ids:
                yield player_id, zone_name, instance_id


def _assert_structural_invariants(state, expected_total: int) -> None:
    entries = list(_iter_zone_entries(state))
    listed = [instance_id for _, _, instance_id in entries]

    # No instance_id lives in two zone lists at once (no duplication).
    assert len(listed) == len(set(listed))
    # Card instances are conserved: none created, destroyed, or orphaned by a move.
    assert set(listed) == set(state.cards)
    assert len(state.cards) == expected_total

    # Each card sits in exactly the (owner, zone) its own fields claim.
    location = {instance_id: (pid, zname) for pid, zname, instance_id in entries}
    for instance_id, card in state.cards.items():
        assert location[instance_id] == (card.owner_id, card.zone.name)


def _census(state) -> dict[tuple[str, str], int]:
    """Reproducible per-zone card counts (instance_ids are non-reproducible uuids)."""
    return {
        (pid, zname): len(zstate.card_ids)
        for pid, player in state.room.players.items()
        for zname, zstate in player.zones.items()
        if zstate.card_ids
    }


def _drive(seed: int, choices: list[int]) -> tuple[list[str], dict[tuple[str, str], int]]:
    engine, state = _build_game(seed=seed)
    total = len(state.cards)

    result = engine.start_game(state)
    assert result.success, result.error
    state = result.state
    _assert_structural_invariants(state, total)

    event_types: list[str] = []
    for choice in choices:
        if result.game_over:
            break
        valid = result.valid_actions
        if not valid:
            break
        # Turn ownership: every offered action belongs to the active player or the pending defender.
        actors = {state.active_player_id, state.pending_defender_id} - {None}
        assert {action["player_id"] for action in valid} <= actors

        # While paused the only *legal* actor is the defender resolving the forced action;
        # get_valid_actions still lists the active player's pass/concede, which the validator rejects.
        required_actor = state.pending_defender_id or state.active_player_id
        pool = [action for action in valid if action["player_id"] == required_actor]
        if not pool:
            break

        chosen = pool[choice % len(pool)]
        result = engine.process_action_from_dict(state, chosen["player_id"], _client_payload(chosen))
        assert result.success, f"action {chosen['action_type']} failed:\n{result.error}"
        state = result.state
        event_types.extend(type(event).__name__ for event in (result.events or []))
        _assert_structural_invariants(state, total)

    return event_types, _census(state)


@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(seed=_seeds, choices=_choices)
def test_structural_invariants_hold_for_any_action_sequence(seed: int, choices: list[int]) -> None:
    _drive(seed, choices)


@settings(max_examples=30, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(seed=_seeds, choices=_choices)
def test_same_seed_and_choices_replay_identically(seed: int, choices: list[int]) -> None:
    events_a, census_a = _drive(seed, choices)
    events_b, census_b = _drive(seed, choices)
    assert events_a == events_b
    assert census_a == census_b
