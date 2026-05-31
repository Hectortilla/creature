from app.models.base.ability import AbilityBase
from app.models.base.association import AssociationBase
from app.models.base.attack import AttackBase
from app.models.base.card import CardBase, CardForeignKeys
from app.models.base.character import CharacterBase
from app.models.base.deck import DeckBase
from app.models.base.element import ElementBase
from app.models.base.type import TypeBase
from app.models.base.user import UserBase

# Re-export core models for convenience
from app.models.core import AttackCoreFields, CardCombatFields, CardIdentityFields
