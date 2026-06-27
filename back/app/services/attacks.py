"""
Attack Service

CRUD operations for attacks with enrichment logic.
"""

from app.models.db.attack import Attack
from app.models.schemas.attack import AttackCreate, AttackReadWithElement
from app.models.schemas.element import ElementRead
from app.services.base import BaseService


def enrich_attack(attack: Attack) -> AttackReadWithElement:
    """Enrich an attack with its element's computed strengths/weaknesses."""
    element_read = None
    strengths = None
    weaknesses = None

    if attack.element:
        element_read = ElementRead.model_validate(attack.element)
        strengths = attack.element.strengths
        weaknesses = attack.element.weaknesses

    return AttackReadWithElement(
        id=attack.id,
        created_at=attack.created_at,
        code=attack.code,
        name=attack.name,
        handle=attack.handle,
        description=attack.description,
        damage=attack.damage,
        type=attack.type,
        element_id=attack.element_id,
        element=element_read,
        dice_rolls=attack.dice_rolls,
        necessary_force=attack.necessary_force,
        effect=attack.effect,
        strengths=strengths,
        weaknesses=weaknesses,
    )


class AttackService(BaseService[Attack, AttackCreate]):
    """Service for Attack CRUD operations with enrichment."""

    model = Attack
    lookup_id_field = "code"
    lookup_str_field = "name"
    has_handle = True

    def enrich(self, attack: Attack) -> AttackReadWithElement:
        """Enrich attack with computed properties."""
        return enrich_attack(attack)

    def get_all_enriched(self) -> list[AttackReadWithElement]:
        """Get all attacks with enriched data."""
        return [enrich_attack(attack) for attack in self.get_all()]

    def get_enriched(self, value: int | str) -> AttackReadWithElement | None:
        """Get attack by code or name with enriched data."""
        attack = self.get(value)
        return enrich_attack(attack) if attack else None
