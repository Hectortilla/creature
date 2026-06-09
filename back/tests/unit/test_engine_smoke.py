"""
End-to-end engine smoke test.

Builds a minimal two-player game with data-driven effects attached, then
drives the engine through many actions, asserting every step succeeds. This
exercises the reducer (element recalculation), the effect/passive query
framework, combat, and the status sweep without needing a database.

Run with:

    uv run pytest tests/unit/test_engine_smoke.py
"""

from __future__ import annotations

import pytest

from app.game.engine import GameEngine
from app.models.game.card import AttackInput, EffectSpec, GameCardInput
from app.models.game.player import PlayerState
from app.models.game.room import GameRoom
from app.models.game.state import GameConfiguration

pytestmark = pytest.mark.unit


def _attack(attack_id: int, name: str, damage: int, element_id: int, type_: str = "physical") -> AttackInput:
    # No necessary_force keeps attacks affordable so combat is reachable in the smoke run.
    return AttackInput(id=attack_id, name=name, damage=damage, type=type_, element_id=element_id)


def _make_deck(owner_tag: str) -> list[GameCardInput]:
    """A small deck whose cards carry a representative spread of effects."""
    cards: list[GameCardInput] = []
    for i in range(8):
        element_id = 3 if i % 2 == 0 else 5  # water / fire
        effect_specs: list[EffectSpec] = []
        if i == 0:
            # Ability stat aura: +10 attack to active allies (exercises STAT_MODIFIER passive).
            effect_specs.append(
                EffectSpec(
                    id=1000 + i,
                    owner_kind="ability",
                    owner_id=900 + i,
                    atom_type="stat-modifier",
                    params={"scope": "allies_active", "attack": 10},
                )
            )
        if i == 1:
            # Attack DoT (exercises status application + turn-start sweep).
            effect_specs.append(
                EffectSpec(
                    id=2000 + i,
                    owner_kind="attack",
                    owner_id=10 + i,
                    atom_type="damage-over-time",
                    trigger="ON_ATTACK_RESOLVE",
                    params={"amount": 5, "duration_turns": 2, "immune_element_id": 6},
                )
            )
        cards.append(
            GameCardInput(
                id=100 + i,
                name=f"{owner_tag}-creature-{i}",
                health=60,
                physical_defence=5,
                magic_defence=5,
                element_ids=[element_id],
                element_contribution=[{"element_id": element_id, "amount": 2}],
                attacks=[_attack(10 + i, f"strike-{i}", damage=20, element_id=element_id)],
                ability_ids=[900 + i] if i == 0 else [],
                effect_specs=effect_specs,
            )
        )
    return cards


def _build_game(seed: int | None = 1234) -> tuple[GameEngine, object]:
    p1 = PlayerState(player_id="p1", name="Player One", deck=_make_deck("p1"))
    p2 = PlayerState(player_id="p2", name="Player Two", deck=_make_deck("p2"))
    room = GameRoom(room_id="room1", host_id="p1")
    room.add_player(p1)
    room.add_player(p2)

    # Seed the per-game RNG here so this suite and the behaviour goldens stay deterministic.
    engine = GameEngine(GameConfiguration(seed=seed))
    state = engine.create_game(room)
    return engine, state


def _act_player_id(state) -> str:
    if state.pending_defender_id:
        return state.pending_defender_id
    return state.active_player_id


def _client_payload(action: dict) -> dict:
    """Reduce an enriched valid-action dict to the fields a real client sends."""
    drop = {"action", "player_id", "valid_phases"}
    return {k: v for k, v in action.items() if k not in drop and not k.endswith("_name")}


def run_smoke(steps: int = 120) -> tuple[int, set[str]]:
    engine, state = _build_game()

    result = engine.start_game(state)
    assert result.success, f"start_game failed: {result.error}"
    state = result.state

    seen_events: set[str] = set()
    actions_taken = 0
    for _ in range(steps):
        if result.game_over:
            break
        valid = result.valid_actions
        assert valid, "engine produced no valid actions"
        # Prefer attacks, then any other substantive action over pass/concede,
        # to drive real transitions (placement → promotion → combat).
        chosen = next(
            (a for a in valid if a["action_type"] == "attack"),
            next((a for a in valid if a["action_type"] not in ("pass", "concede")), valid[0]),
        )
        result = engine.process_action_from_dict(state, _act_player_id(state), _client_payload(chosen))
        assert result.success, f"action {chosen['action_type']} failed:\n{result.error}"
        seen_events.update(type(e).__name__ for e in (result.events or []))
        state = result.state
        actions_taken += 1

    return actions_taken, seen_events


def test_engine_smoke() -> None:
    taken, seen = run_smoke()
    # With the fixed seed the run deterministically reaches combat, the DoT
    # attack status, and the full status lifecycle — guard all of them.
    required = {
        "DamageDealtEvent",
        "AttackResolvedEvent",  # combat
        "StatusAppliedEvent",
        "StatusTickedEvent",
        "StatusExpiredEvent",  # status lifecycle
        "CardHealthChangedEvent",  # damage-over-time tick
    }
    missing = required - seen
    assert not missing, f"smoke run never produced {sorted(missing)}; saw {sorted(seen)}"
    assert taken > 0


if __name__ == "__main__":
    test_engine_smoke()
    print("OK: engine smoke test passed")
