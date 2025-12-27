"""
Attack Models

Models for attack definitions and attack results.
"""

from pydantic import field_serializer

from app.models.core.attack import AttackCoreFields
from app.models.game.base import GameBaseModel
from app.models.game.enums import DamageType
from app.models.game.element import ElementContribution


class AttackDefinition(AttackCoreFields, GameBaseModel):
    """
    Represents an attack that a creature can perform.
    
    Inherits shared fields from AttackCoreFields:
    - name, description, damage, effect, dice_rolls
    
    Adds game-specific fields: attack_id, type (enum), element_id, necessary_force (typed)
    """
    attack_id: int
    # Override damage to be required (not Optional) for game runtime
    damage: int
    # Use DamageType enum instead of str for type safety
    type: DamageType
    element_id: int
    # Use typed ElementContribution instead of dict
    necessary_force: list[ElementContribution] = []
    
    @field_serializer('type')
    def serialize_type(self, value: DamageType) -> str:
        return value.name


class AttackResult(GameBaseModel):
    """
    Result of an attack calculation.
    """
    attacker_id: str
    target_id: str
    attack_id: int
    base_damage: int
    element_bonus: int
    defense_reduction: int
    final_damage: int
    target_destroyed: bool
    attacker_damaged: bool = False
    attacker_damage: int = 0


__all__ = [
    "AttackDefinition",
    "AttackResult",
]

