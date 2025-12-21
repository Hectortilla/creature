from sqlmodel import SQLModel
from datetime import datetime

from app.models.schemas.element import ElementRead
from app.models.schemas.type import TypeRead
from app.models.schemas.character import CharacterRead
from app.models.schemas.attack import AttackReadWithElement
from app.models.schemas.ability import AbilityRead
from app.models.schemas.association import AssociationRead


class CardCreate(SQLModel):
    """Request body for creating a card."""
    code: int
    name: str
    description: str | None = None
    image: str | None = None
    overlay_image: str | None = None
    is_evolution_id: int | None = None
    first_element_id: int | None = None
    second_element_id: int | None = None
    type_id: int | None = None
    character_id: int | None = None
    first_attack_id: int | None = None
    second_attack_id: int | None = None
    ability_id: int | None = None
    association_id: int | None = None
    health: int | None = None
    physical_defence: int | None = None
    magic_defence: int | None = None
    forces: dict | None = None


class CardRead(SQLModel):
    """Response model for a card (lightweight)."""
    id: int
    created_at: datetime
    code: int
    name: str
    handle: str
    description: str | None = None
    image: str | None = None
    overlay_image: str | None = None
    health: int | None = None
    physical_defence: int | None = None
    magic_defence: int | None = None
    forces: list[dict] | None = None
    is_evolution_id: int | None = None
    first_element_id: int | None = None
    second_element_id: int | None = None
    type_id: int | None = None
    character_id: int | None = None
    first_attack_id: int | None = None
    second_attack_id: int | None = None
    ability_id: int | None = None
    association_id: int | None = None


class CardReadWithRelations(CardRead):
    """Response model for a card with all relationships."""
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

