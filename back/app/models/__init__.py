# ORM/Database models
from app.models.db import (
    Element,
    Type,
    Character,
    Ability,
    Association,
    Attack,
    Card,
    Effect,
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
    EffectRead,
)

# Base models (for inheritance - used by db and schema models)
from app.models.base import (
    CharacterBase,
    TypeBase,
    ElementBase,
    AbilityBase,
    AssociationBase,
    AttackBase,
    CardBase,
    CardForeignKeys,
)

# Game state models are in app.models.game submodule
# Import directly: from app.models.game import GameState, GameCard, etc.
# Re-exported via app.game for convenience
