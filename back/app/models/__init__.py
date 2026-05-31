# ORM/Database models
# Base models (for inheritance - used by db and schema models)
from app.models.base import (
    AbilityBase,
    AssociationBase,
    AttackBase,
    CardBase,
    CardForeignKeys,
    CharacterBase,
    ElementBase,
    TypeBase,
)
from app.models.db import (
    Ability,
    Association,
    Attack,
    Card,
    Character,
    Effect,
    Element,
    Type,
)

# Request/Response schemas
from app.models.schemas import (
    AbilityCreate,
    AbilityRead,
    AssociationCreate,
    AssociationRead,
    AttackCreate,
    AttackRead,
    AttackReadWithElement,
    CardCreate,
    CardRead,
    CardReadWithRelations,
    CharacterCreate,
    CharacterRead,
    EffectRead,
    ElementCreate,
    ElementRead,
    TypeCreate,
    TypeRead,
)

# Game state models are in app.models.game submodule
# Import directly: from app.models.game import GameState, GameCard, etc.
# Re-exported via app.game for convenience
