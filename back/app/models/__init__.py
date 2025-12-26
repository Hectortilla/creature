# ORM/Database models
from app.models.db import (
    Element,
    Type,
    Character,
    Ability,
    Association,
    Attack,
    Card,
)

# Request/Response schemas
from app.models.schemas import (
    ElementCreate, ElementRead,
    TypeCreate, TypeRead,
    CharacterCreate, CharacterRead,
    AbilityCreate, AbilityRead,
    AssociationCreate, AssociationRead,
    AttackCreate, AttackRead, AttackReadWithElement,
    CardCreate, CardRead, CardReadWithRelations,
)

# Base models (for inheritance)
from app.models.base import (
    CharacterBase,
    TypeBase,
    ElementBase,
    AbilityBase,
    AssociationBase,
    AttackBase,
    CardBase,
    CardForeignKeys,
    # Game runtime base models (Pydantic)
    GameBaseModel,
    ElementContributionBase,
    AttackCostBase,
    GameCardStats,
    GameConfigurationBase,
)

__all__ = [
    # DB models
    "Element",
    "Type",
    "Character",
    "Ability",
    "Association",
    "Attack",
    "Card",
    # Schemas
    "ElementCreate", "ElementRead",
    "TypeCreate", "TypeRead",
    "CharacterCreate", "CharacterRead",
    "AbilityCreate", "AbilityRead",
    "AssociationCreate", "AssociationRead",
    "AttackCreate", "AttackRead", "AttackReadWithElement",
    "CardCreate", "CardRead", "CardReadWithRelations",
    # Base models
    "CharacterBase",
    "TypeBase",
    "ElementBase",
    "AbilityBase",
    "AssociationBase",
    "AttackBase",
    "CardBase",
    "CardForeignKeys",
    # Game base models (Pydantic)
    "GameBaseModel",
    "ElementContributionBase",
    "AttackCostBase",
    "GameCardStats",
    "GameConfigurationBase",
]
