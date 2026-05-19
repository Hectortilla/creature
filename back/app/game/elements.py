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
    FIRE = 1
    WATER = 2
    EARTH = 3
    AIR = 4
    LIGHT = 5
    DARK = 6
    NATURE = 7
    ELECTRIC = 8
    ICE = 9
    METAL = 10
    POISON = 11
    PSYCHIC = 12
    NEUTRAL = 13


# ── Element interaction matrix ──────────────────────────────────────────
# Key: (attacker_element, defender_element) → bonus (+3 = strong, -3 = weak)
# Missing pairs default to 0 (neutral).

_BONUS = 3
_PENALTY = -3

ELEMENT_BONUS: dict[tuple[int, int], int] = {}

_RELATIONSHIPS: dict[int, tuple[list[int], list[int]]] = {
    # element: (strengths, weaknesses)
    ElementId.FIRE:     ([ElementId.NATURE, ElementId.ICE, ElementId.METAL],      [ElementId.WATER, ElementId.EARTH]),
    ElementId.WATER:    ([ElementId.FIRE, ElementId.EARTH],                        [ElementId.ELECTRIC, ElementId.NATURE]),
    ElementId.EARTH:    ([ElementId.FIRE, ElementId.ELECTRIC, ElementId.POISON],   [ElementId.WATER, ElementId.NATURE, ElementId.ICE]),
    ElementId.AIR:      ([ElementId.EARTH, ElementId.NATURE],                      [ElementId.ELECTRIC, ElementId.ICE]),
    ElementId.LIGHT:    ([ElementId.DARK, ElementId.PSYCHIC],                      [ElementId.DARK]),
    ElementId.DARK:     ([ElementId.LIGHT, ElementId.PSYCHIC],                     [ElementId.LIGHT]),
    ElementId.NATURE:   ([ElementId.WATER, ElementId.EARTH],                       [ElementId.FIRE, ElementId.AIR, ElementId.POISON]),
    ElementId.ELECTRIC: ([ElementId.WATER, ElementId.AIR, ElementId.METAL],        [ElementId.EARTH]),
    ElementId.ICE:      ([ElementId.EARTH, ElementId.AIR, ElementId.NATURE],       [ElementId.FIRE, ElementId.METAL]),
    ElementId.METAL:    ([ElementId.ICE, ElementId.NATURE],                        [ElementId.FIRE, ElementId.ELECTRIC]),
    ElementId.POISON:   ([ElementId.NATURE],                                       [ElementId.EARTH, ElementId.PSYCHIC]),
    ElementId.PSYCHIC:  ([ElementId.POISON],                                       [ElementId.DARK]),
    ElementId.NEUTRAL:  ([],                                                       []),
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
