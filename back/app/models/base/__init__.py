from app.models.base.character import CharacterBase
from app.models.base.type import TypeBase
from app.models.base.element import ElementBase
from app.models.base.ability import AbilityBase
from app.models.base.association import AssociationBase
from app.models.base.attack import AttackBase
from app.models.base.card import CardBase, CardForeignKeys

# Re-export core models for convenience
from app.models.core import CardCombatFields, CardIdentityFields, AttackCoreFields

__all__ = [
    "CharacterBase",
    "TypeBase",
    "ElementBase",
    "AbilityBase",
    "AssociationBase",
    "AttackBase",
    "CardBase",
    "CardForeignKeys",
    # Core field definitions
    "CardCombatFields",
    "CardIdentityFields", 
    "AttackCoreFields",
]
