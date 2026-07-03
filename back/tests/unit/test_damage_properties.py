"""Property-based invariants over the combat math.

Complements the numeric pins in ``test_damage_math.py``: those pin a handful of
rows, these assert the properties that must hold across the *whole* input space,
so a sign flip or off-by-one outside the pinned rows can't ship green. Pure math,
no DB. Cross-checks the element matrix against the live data in
``app/game/elements.py`` rather than hand-copying values.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.game.elements import (
    ElementId,
    calculate_damage,
    get_element_bonus,
    get_total_element_bonus,
)
from app.models.game.attack import AttackDefinition
from app.models.game.card import GameCard
from app.models.game.enums import DamageType

pytestmark = pytest.mark.unit

_elements = st.sampled_from(list(ElementId))
_defenders = st.lists(_elements, max_size=4)
_damage = st.integers(min_value=0, max_value=200)
_effect = st.integers(min_value=-50, max_value=50)
_defense = st.integers(min_value=0, max_value=200)

_ATTACKER = GameCard.create(
    card_id=99, owner_id="p1", name="attacker", health=999, physical_defence=0, magic_defence=0, element_ids=[]
)


def _attack(element_id: int, damage: int, type_: DamageType = DamageType.PHYSICAL) -> AttackDefinition:
    return AttackDefinition(attack_id=1, name="a", damage=damage, type=type_, element_id=int(element_id))


def _target(element_ids: list[int], physical_defence: int, magic_defence: int = 0) -> GameCard:
    return GameCard.create(
        card_id=1,
        owner_id="p2",
        name="target",
        health=999,
        physical_defence=physical_defence,
        magic_defence=magic_defence,
        element_ids=[int(e) for e in element_ids],
    )


# ── Damage calculation properties ────────────────────────────────────────


@settings(max_examples=200, deadline=None)
@given(element=_elements, defenders=_defenders, damage=_damage, effect=_effect, defense=_defense)
def test_final_damage_never_negative_and_reflection_is_the_shortfall(
    element: int, defenders: list[int], damage: int, effect: int, defense: int
) -> None:
    calc = calculate_damage(_attack(element, damage), _ATTACKER, _target(defenders, defense), effect_modifier=effect)

    assert calc.final_damage >= 0
    assert calc.reflected_damage >= 0
    # A single attack either lands damage or reflects the overkill — never both.
    assert not (calc.final_damage > 0 and calc.reflected_damage > 0)
    assert calc.final_damage == max(0, calc.pre_defense_damage - defense)
    assert calc.reflected_damage == max(0, defense - calc.pre_defense_damage)


@settings(max_examples=200, deadline=None)
@given(element=_elements, defenders=_defenders, damage=_damage, effect=_effect, defense=_defense)
def test_element_bonus_is_added_before_defense_is_subtracted(
    element: int, defenders: list[int], damage: int, effect: int, defense: int
) -> None:
    target = _target(defenders, defense)
    calc = calculate_damage(_attack(element, damage), _ATTACKER, target, effect_modifier=effect)

    assert calc.element_bonus == get_total_element_bonus(int(element), target.element_ids)
    assert calc.pre_defense_damage == calc.base_damage + calc.element_bonus + calc.effect_modifiers
    assert calc.final_damage == max(0, calc.pre_defense_damage - calc.defense_value)


@settings(max_examples=200, deadline=None)
@given(
    element=_elements,
    defenders=_defenders,
    damage=_damage,
    effect=_effect,
    defense_a=_defense,
    defense_b=_defense,
)
def test_higher_defense_never_increases_final_damage(
    element: int, defenders: list[int], damage: int, effect: int, defense_a: int, defense_b: int
) -> None:
    low, high = sorted((defense_a, defense_b))
    calc_low = calculate_damage(_attack(element, damage), _ATTACKER, _target(defenders, low), effect_modifier=effect)
    calc_high = calculate_damage(_attack(element, damage), _ATTACKER, _target(defenders, high), effect_modifier=effect)

    assert calc_high.final_damage <= calc_low.final_damage
    assert calc_high.reflected_damage >= calc_low.reflected_damage


@settings(max_examples=200, deadline=None)
@given(element=_elements, damage=_damage, physical=_defense, magical=_defense)
def test_damage_type_selects_the_matching_defense(element: int, damage: int, physical: int, magical: int) -> None:
    target = _target([element], physical_defence=physical, magic_defence=magical)

    physical_calc = calculate_damage(_attack(element, damage, DamageType.PHYSICAL), _ATTACKER, target)
    magical_calc = calculate_damage(_attack(element, damage, DamageType.MAGICAL), _ATTACKER, target)

    assert physical_calc.defense_value == physical
    assert magical_calc.defense_value == magical


# ── Element matrix properties ─────────────────────────────────────────────


def test_element_matrix_is_internally_consistent() -> None:
    for attacker in ElementId:
        for defender in ElementId:
            bonus = get_element_bonus(attacker, defender)
            assert bonus in (-3, 0, 3)
            # Directional advantage is antisymmetric: A can't be strong vs B while B is strong vs A.
            if attacker != defender and bonus == 3:
                assert get_element_bonus(defender, attacker) != 3


@settings(max_examples=100, deadline=None)
@given(element=_elements, defenders=_defenders)
def test_total_element_bonus_is_the_sum_of_pairwise_bonuses(element: int, defenders: list[int]) -> None:
    expected = sum(get_element_bonus(int(element), int(d)) for d in defenders)
    assert get_total_element_bonus(int(element), [int(d) for d in defenders]) == expected


def test_total_element_bonus_of_no_defenders_is_zero() -> None:
    for element in ElementId:
        assert get_total_element_bonus(int(element), []) == 0
