"""
Element System

Implements the element interaction matrix and damage calculations
based on element strengths and weaknesses.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional
from enum import IntEnum

if TYPE_CHECKING:
    from app.models.game import GameCard, AttackDefinition


class ElementId(IntEnum):
    """
    Standard element IDs.
    
    These should match the database element IDs.
    """
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


@dataclass
class ElementInteraction:
    """
    Defines interaction between two elements.
    
    Attributes:
        attacking_element: The element of the attack
        defending_element: The element of the defender
        bonus: Damage bonus/penalty (-10 to +10 typical range)
                Positive = attacker has advantage
                Negative = defender has advantage
    """
    attacking_element: int
    defending_element: int
    bonus: int


class ElementMatrix:
    """
    Manages element interaction calculations.
    
    The matrix defines how each element interacts with every other element.
    Bonuses/penalties are applied to damage based on attack element vs
    defender's elements.
    """
    
    # Default strength bonus
    STRENGTH_BONUS = 3
    # Default weakness penalty
    WEAKNESS_PENALTY = -3
    # Neutral (no relationship)
    NEUTRAL_BONUS = 0
    
    def __init__(self):
        """Initialize with default element interactions."""
        self._matrix: dict[tuple[int, int], int] = {}
        self._strengths: dict[int, list[int]] = {}
        self._weaknesses: dict[int, list[int]] = {}
        self._setup_default_matrix()
    
    def _setup_default_matrix(self) -> None:
        """
        Setup default element interactions.
        
        This can be overridden or extended by loading from database.
        """
        # Default classical element relationships
        default_relationships = {
            # Fire
            ElementId.FIRE: {
                "strengths": [ElementId.NATURE, ElementId.ICE, ElementId.METAL],
                "weaknesses": [ElementId.WATER, ElementId.EARTH],
            },
            # Water
            ElementId.WATER: {
                "strengths": [ElementId.FIRE, ElementId.EARTH],
                "weaknesses": [ElementId.ELECTRIC, ElementId.NATURE],
            },
            # Earth
            ElementId.EARTH: {
                "strengths": [ElementId.FIRE, ElementId.ELECTRIC, ElementId.POISON],
                "weaknesses": [ElementId.WATER, ElementId.NATURE, ElementId.ICE],
            },
            # Air
            ElementId.AIR: {
                "strengths": [ElementId.EARTH, ElementId.NATURE],
                "weaknesses": [ElementId.ELECTRIC, ElementId.ICE],
            },
            # Light
            ElementId.LIGHT: {
                "strengths": [ElementId.DARK, ElementId.PSYCHIC],
                "weaknesses": [ElementId.DARK],  # Mutual
            },
            # Dark
            ElementId.DARK: {
                "strengths": [ElementId.LIGHT, ElementId.PSYCHIC],
                "weaknesses": [ElementId.LIGHT],  # Mutual
            },
            # Nature
            ElementId.NATURE: {
                "strengths": [ElementId.WATER, ElementId.EARTH],
                "weaknesses": [ElementId.FIRE, ElementId.AIR, ElementId.POISON],
            },
            # Electric
            ElementId.ELECTRIC: {
                "strengths": [ElementId.WATER, ElementId.AIR, ElementId.METAL],
                "weaknesses": [ElementId.EARTH],
            },
            # Ice
            ElementId.ICE: {
                "strengths": [ElementId.EARTH, ElementId.AIR, ElementId.NATURE],
                "weaknesses": [ElementId.FIRE, ElementId.METAL],
            },
            # Metal
            ElementId.METAL: {
                "strengths": [ElementId.ICE, ElementId.NATURE],
                "weaknesses": [ElementId.FIRE, ElementId.ELECTRIC],
            },
            # Poison
            ElementId.POISON: {
                "strengths": [ElementId.NATURE],
                "weaknesses": [ElementId.EARTH, ElementId.PSYCHIC],
            },
            # Psychic
            ElementId.PSYCHIC: {
                "strengths": [ElementId.POISON],
                "weaknesses": [ElementId.DARK],
            },
            # Neutral - no special relationships
            ElementId.NEUTRAL: {
                "strengths": [],
                "weaknesses": [],
            },
        }
        
        # Build the matrix
        for attacker, relations in default_relationships.items():
            self._strengths[attacker] = relations["strengths"]
            self._weaknesses[attacker] = relations["weaknesses"]
            
            for defender in relations["strengths"]:
                self._matrix[(attacker, defender)] = self.STRENGTH_BONUS
            
            for defender in relations["weaknesses"]:
                self._matrix[(attacker, defender)] = self.WEAKNESS_PENALTY
    
    def load_from_database(self, elements: list[dict]) -> None:
        """
        Load element relationships from database records.
        
        Args:
            elements: List of element dicts with 'id', 'strengths', 'weaknesses'
        """
        self._matrix.clear()
        self._strengths.clear()
        self._weaknesses.clear()
        
        for elem in elements:
            elem_id = elem["id"]
            strengths = elem.get("strengths") or []
            weaknesses = elem.get("weaknesses") or []
            
            self._strengths[elem_id] = strengths
            self._weaknesses[elem_id] = weaknesses
            
            for target in strengths:
                self._matrix[(elem_id, target)] = self.STRENGTH_BONUS
            
            for target in weaknesses:
                self._matrix[(elem_id, target)] = self.WEAKNESS_PENALTY
    
    def get_interaction(self, attacking_element: int, defending_element: int) -> int:
        """
        Get the damage bonus/penalty for an element interaction.
        
        Args:
            attacking_element: Element ID of the attack
            defending_element: Element ID of the defender
        
        Returns:
            Bonus (positive) or penalty (negative) value
        """
        return self._matrix.get((attacking_element, defending_element), self.NEUTRAL_BONUS)
    
    def get_total_bonus(self, attacking_element: int, defending_elements: list[int]) -> int:
        """
        Calculate total element bonus against a target with multiple elements.
        
        As per rules, bonuses/penalties are summed for all defender elements.
        
        Args:
            attacking_element: Element ID of the attack
            defending_elements: List of element IDs on the defender
        
        Returns:
            Total bonus (sum of all interactions)
        """
        total = 0
        for def_elem in defending_elements:
            total += self.get_interaction(attacking_element, def_elem)
        return total
    
    def is_strong_against(self, element: int, target: int) -> bool:
        """Check if element is strong against target."""
        return target in self._strengths.get(element, [])
    
    def is_weak_against(self, element: int, target: int) -> bool:
        """Check if element is weak against target."""
        return target in self._weaknesses.get(element, [])
    
    def get_strengths(self, element: int) -> list[int]:
        """Get elements this element is strong against."""
        return self._strengths.get(element, [])
    
    def get_weaknesses(self, element: int) -> list[int]:
        """Get elements this element is weak against."""
        return self._weaknesses.get(element, [])


# Global element matrix instance
_element_matrix: Optional[ElementMatrix] = None


def get_element_matrix() -> ElementMatrix:
    """Get or create the global element matrix instance."""
    global _element_matrix
    if _element_matrix is None:
        _element_matrix = ElementMatrix()
    return _element_matrix


def calculate_element_bonus(
    attack_element: int,
    target_elements: list[int],
    matrix: Optional[ElementMatrix] = None
) -> int:
    """
    Calculate element bonus/penalty for an attack.
    
    Args:
        attack_element: Element ID of the attack
        target_elements: Element IDs of the target creature
        matrix: Optional custom element matrix (uses global if not provided)
    
    Returns:
        Total bonus (positive) or penalty (negative)
    """
    if matrix is None:
        matrix = get_element_matrix()
    return matrix.get_total_bonus(attack_element, target_elements)


@dataclass
class DamageCalculation:
    """
    Complete damage calculation breakdown.
    
    Attributes:
        base_damage: Base damage from the attack
        element_bonus: Bonus/penalty from element interactions
        effect_modifiers: Additional modifiers from effects
        defense_value: Defense value of the target
        pre_defense_damage: Damage before defense is applied
        final_damage: Final damage dealt to target
        reflected_damage: Damage reflected back to attacker (if any)
    """
    base_damage: int
    element_bonus: int
    effect_modifiers: int = 0
    defense_value: int = 0
    pre_defense_damage: int = 0
    final_damage: int = 0
    reflected_damage: int = 0
    
    def __post_init__(self):
        """Calculate derived values."""
        self.pre_defense_damage = self.base_damage + self.element_bonus + self.effect_modifiers
        self.final_damage = self.pre_defense_damage - self.defense_value
        
        # If final damage is negative, the attacker takes that damage
        if self.final_damage < 0:
            self.reflected_damage = abs(self.final_damage)
            self.final_damage = 0


def calculate_damage(
    attack: "AttackDefinition",
    attacker: "GameCard",
    target: "GameCard",
    effect_modifier: int = 0,
    matrix: Optional[ElementMatrix] = None
) -> DamageCalculation:
    """
    Calculate damage for an attack.
    
    Implementation of the damage formula from the rules:
    1. Base damage from attack
    2. Add element interaction bonus/penalty
    3. Add effect modifiers
    4. Subtract target's defense (physical or magical based on attack type)
    5. If negative, damage is dealt to attacker instead
    
    Args:
        attack: The attack being used
        attacker: The attacking card
        target: The target card
        effect_modifier: Additional damage modifier from effects
        matrix: Optional custom element matrix
    
    Returns:
        DamageCalculation with full breakdown
    """
    from app.game.enums import DamageType
    
    # Get base damage
    base_damage = attack.base_damage
    
    # Calculate element bonus
    element_bonus = calculate_element_bonus(
        attack.element_id,
        target.element_ids,
        matrix
    )
    
    # Get appropriate defense
    if attack.damage_type == DamageType.PHYSICAL:
        defense = target.physical_defense
    else:  # MAGICAL
        defense = target.magical_defense
    
    return DamageCalculation(
        base_damage=base_damage,
        element_bonus=element_bonus,
        effect_modifiers=effect_modifier,
        defense_value=defense,
    )


def can_afford_attack(
    player_elements: dict[int, int],
    attack: "AttackDefinition"
) -> bool:
    """
    Check if a player can afford the element cost of an attack.
    
    Args:
        player_elements: Dict of element_id -> available amount
        attack: The attack to check
    
    Returns:
        True if the player has enough elements
    """
    for cost in attack.element_cost:
        available = player_elements.get(cost.element_id, 0)
        if available < cost.amount:
            return False
    return True

