"""
Element System

Element interaction bonuses and damage calculation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from enum import IntEnum

if TYPE_CHECKING:
    from app.models.game import GameCard, AttackDefinition


class ElementId(IntEnum):
    ETHER = 1
    EARTH = 2
    WATER = 3
    AIR = 4
    FIRE = 5
    ICE = 6
    THUNDER = 7
    METAL = 8
    NATURE = 9
    TOXIC = 10
    MENTAL = 11
    LIGHT = 12
    DARKNESS = 13


# ── Element interaction matrix ──────────────────────────────────────────
# Key: (attacker_element, defender_element) → bonus (+3 = strong, -3 = weak)
# Missing pairs default to 0 (neutral).

_BONUS = 3
_PENALTY = -3

ELEMENT_BONUS: dict[tuple[int, int], int] = {}

_RELATIONSHIPS: dict[int, tuple[list[int], list[int]]] = {
    # element: (strengths, weaknesses)
    ElementId.ETHER:    ([ElementId.MENTAL],                                       [ElementId.LIGHT]),
    ElementId.EARTH:    ([ElementId.THUNDER, ElementId.METAL],                     [ElementId.WATER, ElementId.NATURE]),
    ElementId.WATER:    ([ElementId.EARTH, ElementId.FIRE],                        [ElementId.THUNDER, ElementId.NATURE]),
    ElementId.AIR:      ([ElementId.FIRE, ElementId.NATURE],                       [ElementId.EARTH, ElementId.THUNDER]),
    ElementId.FIRE:     ([ElementId.ICE, ElementId.NATURE],                        [ElementId.WATER, ElementId.AIR]),
    ElementId.ICE:      ([ElementId.AIR, ElementId.NATURE],                        [ElementId.FIRE, ElementId.METAL]),
    ElementId.THUNDER:  ([ElementId.WATER, ElementId.ICE],                         [ElementId.EARTH, ElementId.METAL]),
    ElementId.METAL:    ([ElementId.ICE, ElementId.MENTAL],                        [ElementId.EARTH, ElementId.NATURE]),
    ElementId.NATURE:   ([ElementId.METAL, ElementId.LIGHT],                       [ElementId.FIRE, ElementId.ICE]),
    ElementId.TOXIC:    ([ElementId.NATURE, ElementId.TOXIC],                      [ElementId.EARTH, ElementId.MENTAL]),
    ElementId.MENTAL:   ([ElementId.TOXIC, ElementId.MENTAL],                      [ElementId.DARKNESS, ElementId.MENTAL]),
    ElementId.LIGHT:    ([ElementId.ETHER],                                        [ElementId.DARKNESS, ElementId.NATURE]),
    ElementId.DARKNESS: ([ElementId.LIGHT],                                        [ElementId.ETHER, ElementId.METAL]),
}

for _atk, (_strengths, _weaknesses) in _RELATIONSHIPS.items():
    for _def in _strengths:
        ELEMENT_BONUS[(_atk, _def)] = _BONUS
    for _def in _weaknesses:
        ELEMENT_BONUS[(_atk, _def)] = _PENALTY


def get_element_bonus(attack_element: int, defender_element: int) -> int:
    """Single attacker-element vs single defender-element bonus."""
    return ELEMENT_BONUS.get((attack_element, defender_element), 0)


def get_total_element_bonus(attack_element: int, defender_elements: list[int]) -> int:
    """Sum of bonuses across all defender elements."""
    return sum(get_element_bonus(attack_element, d) for d in defender_elements)


# ── Damage calculation ──────────────────────────────────────────────────

@dataclass
class DamageCalculation:
    """Full damage breakdown for one attack."""
    base_damage: int
    element_bonus: int
    effect_modifiers: int = 0
    defense_value: int = 0
    pre_defense_damage: int = 0
    final_damage: int = 0
    reflected_damage: int = 0

    def __post_init__(self):
        self.pre_defense_damage = self.base_damage + self.element_bonus + self.effect_modifiers
        self.final_damage = self.pre_defense_damage - self.defense_value
        if self.final_damage < 0:
            self.reflected_damage = abs(self.final_damage)
            self.final_damage = 0


def calculate_damage(
    attack: "AttackDefinition",
    attacker: "GameCard",
    target: "GameCard",
    effect_modifier: int = 0,
) -> DamageCalculation:
    """
    Calculate damage for an attack.

    Formula (per game rules):
        1. Base damage from attack
        2. + element interaction bonus/penalty
        3. + effect modifiers
        4. - target's defense (physical or magical)
        5. If negative → attacker takes that damage instead
    """
    from app.models.game import DamageType

    element_bonus = get_total_element_bonus(attack.element_id, target.element_ids)
    defense = target.physical_defence if attack.type == DamageType.PHYSICAL else target.magic_defence

    return DamageCalculation(
        base_damage=attack.damage,
        element_bonus=element_bonus,
        effect_modifiers=effect_modifier,
        defense_value=defense,
    )


def can_afford_attack(player_elements: dict[int, int], attack: "AttackDefinition") -> bool:
    """Check if a player has enough elements to pay for an attack."""
    for cost in attack.necessary_force:
        if player_elements.get(cost.element_id, 0) < cost.amount:
            return False
    return True
