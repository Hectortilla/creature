"""
Shared Card Field Definitions

These classes define fields shared between CardBase (SQLModel) and GameCard (Pydantic).
They use pure Pydantic so they're compatible with both SQLModel and regular Pydantic models.
"""

from pydantic import BaseModel


class CardIdentityFields(BaseModel):
    """
    Card identity fields shared across all card representations.
    
    Used by:
    - CardBase (database model)
    - GameCard (runtime game model)
    """
    name: str
    description: str | None = None


class CardCombatFields(BaseModel):
    """
    Combat-related fields shared across all card representations.
    
    Used by:
    - CardBase (database model) 
    - GameCard (runtime game model)
    
    Note: In GameCard, 'health' represents max health, with a separate
    'current_health' field for runtime state.
    """
    health: int | None = None
    physical_defence: int | None = None
    magic_defence: int | None = None


