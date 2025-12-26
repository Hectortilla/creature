from app.models.base.character import CharacterBase
from app.models.base.type import TypeBase
from app.models.base.element import ElementBase
from app.models.base.ability import AbilityBase
from app.models.base.association import AssociationBase
from app.models.base.attack import AttackBase
from app.models.base.card import CardBase, CardForeignKeys
from app.models.base.game import (
    GameBaseModel,
    ElementContributionBase,
    AttackCostBase,
    GameCardStats,
    GameConfigurationBase,
)

__all__ = [
    # Entity base models
    "CharacterBase",
    "TypeBase",
    "ElementBase",
    "AbilityBase",
    "AssociationBase",
    "AttackBase",
    "CardBase",
    "CardForeignKeys",
    # Game runtime base models (Pydantic)
    "GameBaseModel",
    "ElementContributionBase",
    "AttackCostBase",
    "GameCardStats",
    "GameConfigurationBase",
]

