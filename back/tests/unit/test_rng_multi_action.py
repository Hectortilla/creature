"""Multi-action RNG determinism: the per-game ``GameState.rng`` must survive a whole
action sequence, not just the opening deal.

The engine mutates state in place and returns the same live object, so the ``_rng``
``PrivateAttr`` is never dropped between ``process_action`` calls. Cards carry a
dice-gated effect so real dice roll mid-sequence — same seed ⇒ identical dice + final
rng position; a different seed diverges.
"""

from __future__ import annotations

import pytest

from app.game.engine import GameEngine
from app.models.game.card import EffectSpec, GameCardInput
from app.models.game.events import DiceRolledEvent
from app.models.game.player import PlayerState
from app.models.game.room import GameRoom
from app.models.game.state import GameConfiguration
from tests.unit.test_engine_smoke import _act_player_id, _client_payload, _make_deck

pytestmark = pytest.mark.unit


def _make_dice_deck(owner_tag: str) -> list[GameCardInput]:
    """The smoke deck, plus a dice-gated apply-status effect on every attack.

    ``dice_face=7`` (``faces=6``) can never match, so each attack rolls a die
    (emitting ``DiceRolledEvent``) without otherwise altering combat.
    """
    cards = _make_deck(owner_tag)
    for card in cards:
        for attack in card.attacks:
            card.effect_specs.append(
                EffectSpec(
                    id=3000 + attack.id,
                    owner_kind="attack",
                    owner_id=attack.id,
                    atom_type="apply-status",
                    trigger="ON_ATTACK_RESOLVE",
                    params={"dice_face": 7, "faces": 6, "purpose": "determinism_probe"},
                )
            )
    return cards


def _build_dice_game(seed: int | None) -> tuple[GameEngine, object]:
    p1 = PlayerState(player_id="p1", name="Player One", deck=_make_dice_deck("p1"))
    p2 = PlayerState(player_id="p2", name="Player Two", deck=_make_dice_deck("p2"))
    room = GameRoom(room_id="room1", host_id="p1")
    room.add_player(p1)
    room.add_player(p2)
    engine = GameEngine(GameConfiguration(seed=seed))
    state = engine.create_game(room)
    return engine, state


def _drive(seed: int | None, steps: int = 120) -> tuple[list[int], tuple, bool]:
    """Drive a deterministic action sequence; capture dice + final rng position.

    Returns ``(dice, final_rng.getstate(), rng_object_stable)``; the last is True
    iff the live ``state.rng`` survives every ``process_action`` (in-place guard).
    """
    engine, state = _build_dice_game(seed=seed)
    result = engine.start_game(state)
    assert result.success, result.error
    state = result.state

    rng_obj = state.rng
    rng_stable = True
    dice: list[int] = []
    for _ in range(steps):
        if result.game_over:
            break
        valid = result.valid_actions
        if not valid:
            break
        chosen = next(
            (a for a in valid if a["action_type"] == "attack"),
            next((a for a in valid if a["action_type"] not in ("pass", "concede")), valid[0]),
        )
        result = engine.process_action_from_dict(state, _act_player_id(state), _client_payload(chosen))
        assert result.success, f"action {chosen['action_type']} failed:\n{result.error}"
        state = result.state
        if state.rng is not rng_obj:
            rng_stable = False
        dice.extend(e.result for e in (result.events or []) if isinstance(e, DiceRolledEvent))

    return dice, state.rng.getstate(), rng_stable


def test_same_seed_reproduces_dice_across_actions() -> None:
    dice_a, rng_a, stable_a = _drive(2026)
    dice_b, rng_b, stable_b = _drive(2026)

    # The sequence must actually roll dice mid-game, or it proves nothing.
    assert dice_a, "expected DiceRolledEvents during the action sequence"
    assert dice_a == dice_b
    # The live rng advanced identically across the whole sequence.
    assert rng_a == rng_b
    # The PrivateAttr rng object was never dropped/rehydrated between actions.
    assert stable_a and stable_b


def test_different_seed_changes_dice() -> None:
    dice_a, *_ = _drive(2026)
    dice_c, *_ = _drive(1789)
    assert dice_a != dice_c
