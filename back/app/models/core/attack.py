"""
Shared Attack Field Definitions

These classes define fields shared between AttackBase (SQLModel) and AttackDefinition (Pydantic).
They use pure Pydantic so they're compatible with both SQLModel and regular Pydantic models.
"""

from pydantic import BaseModel


class AttackCoreFields(BaseModel):
    """
    Core attack fields shared across all attack representations.
    
    Used by:
    - AttackBase (database model)
    - AttackDefinition (runtime game model)
    
    Note: 
    - 'type' is str in AttackBase but DamageType enum in AttackDefinition
    - 'necessary_force' is list[dict] in AttackBase but list[ElementContribution] in AttackDefinition
    
    These type differences are handled by the inheriting classes.
    """
    name: str
    description: str | None = None
    damage: int | None = None
    effect: str | None = None
    dice_rolls: int | None = None





