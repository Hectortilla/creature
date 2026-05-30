from datetime import datetime
from pydantic import Field

from app.models.base.card import CardBase, CardForeignKeys
from app.models.schemas.element import ElementRead
from app.models.schemas.type import TypeRead
from app.models.schemas.character import CharacterRead
from app.models.schemas.attack import AttackReadWithElement
from app.models.schemas.ability import AbilityRead
from app.models.schemas.association import AssociationRead
from app.models.schemas.effect import EffectRead


class CardCreate(CardBase, CardForeignKeys):
    pass


class CardRead(CardBase, CardForeignKeys):
    id: int
    created_at: datetime
    handle: str
    forces: list[dict] | None = None  # Override to allow list format in response


class CardReadWithRelations(CardRead):
    first_element: ElementRead | None = None
    second_element: ElementRead | None = None
    type: TypeRead | None = None
    character: CharacterRead | None = None
    first_attack: AttackReadWithElement | None = None
    second_attack: AttackReadWithElement | None = None
    ability: AbilityRead | None = None
    association: AssociationRead | None = None
    is_evolution: "CardRead | None" = None
    next_evolutions: list["CardRead"] | None = None
    strengths: list[int] | None = None
    weaknesses: list[int] | None = None
    effects: list[EffectRead] = Field(default_factory=list)
