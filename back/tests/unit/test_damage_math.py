"""Numeric pins for the combat math: element bonuses, damage calculation, and
validator rejection paths.

These hand-assert concrete values so a wrong damage formula, a flipped
element-bonus sign, the wrong defense being subtracted, or a broken
overkill-reflection branch fails here even if the behaviour golden is
re-baselined. No database required.

    uv run pytest tests/unit/test_damage_math.py
"""

from __future__ import annotations

import pytest

from app.game.actions.combat import AttackAction
from app.game.elements import (
    ElementId,
    calculate_damage,
    get_element_bonus,
    get_total_element_bonus,
)
from app.game.validators import RuleValidator
from app.models.game.attack import AttackDefinition
from app.models.game.card import GameCard
from app.models.game.enums import DamageType, GameStatus, TurnPhase
from app.models.game.player import PlayerState
from app.models.game.room import GameRoom
from app.models.game.state import GameState

pytestmark = pytest.mark.unit

F, ICE, NATURE, WATER, AIR, ETHER = (
    ElementId.FIRE,
    ElementId.ICE,
    ElementId.NATURE,
    ElementId.WATER,
    ElementId.AIR,
    ElementId.ETHER,
)


def _attack(element_id: int = ETHER, damage: int = 20, type_: DamageType = DamageType.PHYSICAL) -> AttackDefinition:
    return AttackDefinition(attack_id=1, name="a", damage=damage, type=type_, element_id=element_id)


def _target(element_ids: list[int], physical_defence: int = 5, magic_defence: int = 5) -> GameCard:
    return GameCard.create(
        card_id=1,
        owner_id="p2",
        name="target",
        health=50,
        physical_defence=physical_defence,
        magic_defence=magic_defence,
        element_ids=element_ids,
    )


# ── Element interaction matrix ───────────────────────────────────────────


@pytest.mark.parametrize(
    "attack_element, defender_element, expected",
    [
        (F, ICE, 3),  # fire is strong against ice
        (F, NATURE, 3),  # fire is strong against nature
        (F, WATER, -3),  # fire is weak against water
        (F, AIR, -3),  # fire is weak against air
        (F, F, 0),  # same element is neutral
        (F, ETHER, 0),  # unrelated pair defaults to neutral
        (WATER, F, 3),  # relationship is directional: water beats fire
    ],
)
def test_get_element_bonus(attack_element: int, defender_element: int, expected: int) -> None:
    assert get_element_bonus(attack_element, defender_element) == expected


@pytest.mark.parametrize(
    "attack_element, defender_elements, expected",
    [
        (F, [], 0),
        (F, [ICE, NATURE], 6),  # two strengths stack
        (F, [WATER, AIR], -6),  # two weaknesses stack
        (F, [ICE, WATER], 0),  # strength and weakness cancel
        (F, [ETHER], 0),
    ],
)
def test_get_total_element_bonus(attack_element: int, defender_elements: list[int], expected: int) -> None:
    assert get_total_element_bonus(attack_element, defender_elements) == expected


def test_element_bonus_lookup_does_not_drift() -> None:
    # Repeated queries must be stable — the shared matrix must never be mutated.
    assert get_element_bonus(F, ICE) == 3
    assert get_element_bonus(F, ICE) == 3
    assert get_total_element_bonus(F, [ICE, NATURE]) == 6


# ── Damage calculation ───────────────────────────────────────────────────


@pytest.mark.parametrize(
    "attack, target, expected",
    [
        # (element_bonus, pre_defense_damage, final_damage, reflected_damage)
        (_attack(ETHER), _target([ETHER]), (0, 20, 15, 0)),  # neutral, physical defense
        (_attack(F), _target([ICE]), (3, 23, 18, 0)),  # strong element adds before defense
        (_attack(F), _target([WATER]), (-3, 17, 12, 0)),  # weak element subtracts
        (_attack(F), _target([ICE, NATURE]), (6, 26, 21, 0)),  # stacked element bonus
        (
            _attack(F, type_=DamageType.MAGICAL),
            _target([ETHER], physical_defence=100, magic_defence=8),
            (0, 20, 12, 0),
        ),  # magical uses magic_defence
        (
            _attack(ETHER, damage=10),
            _target([ETHER], physical_defence=20),
            (0, 10, 0, 10),
        ),  # overkill reflects, floors at 0
    ],
)
def test_calculate_damage(attack: AttackDefinition, target: GameCard, expected: tuple[int, int, int, int]) -> None:
    attacker = _target([ETHER])
    calc = calculate_damage(attack, attacker, target)
    assert (calc.element_bonus, calc.pre_defense_damage, calc.final_damage, calc.reflected_damage) == expected


def test_calculate_damage_applies_effect_modifier() -> None:
    calc = calculate_damage(_attack(ETHER), _target([ETHER]), _target([ETHER]), effect_modifier=10)
    assert calc.pre_defense_damage == 30  # base 20 + 0 element + 10 effect
    assert calc.final_damage == 25  # minus physical defense 5


# ── Validator rejection paths ────────────────────────────────────────────


def _state(status: GameStatus, phase: TurnPhase) -> GameState:
    room = GameRoom(room_id="r", host_id="p1")
    room.add_player(PlayerState(player_id="p1", name="P1", deck=[]))
    room.add_player(PlayerState(player_id="p2", name="P2", deck=[]))
    state = GameState.create(room)
    state.status = status
    state.active_player_id = "p1"
    state.current_phase = phase
    return state


def test_reject_when_game_not_in_progress() -> None:
    state = _state(GameStatus.WAITING, TurnPhase.ATTACK)
    result = RuleValidator().validate(state, AttackAction(player_id="p1"))
    assert result.valid is False
    assert result.error_code == "GAME_NOT_IN_PROGRESS"


def test_reject_when_not_your_turn() -> None:
    state = _state(GameStatus.IN_PROGRESS, TurnPhase.ATTACK)
    result = RuleValidator().validate(state, AttackAction(player_id="p2"))
    assert result.valid is False
    assert result.error_code == "NOT_YOUR_TURN"


def test_reject_attack_in_wrong_phase() -> None:
    state = _state(GameStatus.IN_PROGRESS, TurnPhase.DRAW)
    result = RuleValidator().validate(state, AttackAction(player_id="p1"))
    assert result.valid is False
    assert result.error_code == "WRONG_PHASE"
