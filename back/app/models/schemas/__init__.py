from app.models.schemas.element import ElementCreate, ElementRead
from app.models.schemas.type import TypeCreate, TypeRead
from app.models.schemas.character import CharacterCreate, CharacterRead
from app.models.schemas.ability import AbilityCreate, AbilityRead
from app.models.schemas.association import AssociationCreate, AssociationRead
from app.models.schemas.attack import AttackCreate, AttackRead, AttackReadWithElement
from app.models.schemas.card import CardCreate, CardRead, CardReadWithRelations

__all__ = [
    "ElementCreate", "ElementRead",
    "TypeCreate", "TypeRead",
    "CharacterCreate", "CharacterRead",
    "AbilityCreate", "AbilityRead",
    "AssociationCreate", "AssociationRead",
    "AttackCreate", "AttackRead", "AttackReadWithElement",
    "CardCreate", "CardRead", "CardReadWithRelations",
]

