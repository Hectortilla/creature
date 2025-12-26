from sqlmodel import SQLModel, Field

from app.models.core.card import CardIdentityFields, CardCombatFields


class CardBase(CardIdentityFields, CardCombatFields, SQLModel):
    """
    Base card model for database.
    
    Inherits shared fields from:
    - CardIdentityFields: name, description
    - CardCombatFields: health, physical_defence, magic_defence
    
    Adds DB-specific fields: code, image, overlay_image, forces
    """
    code: int
    # Override with Field constraints for DB
    name: str = Field(max_length=255)
    image: str | None = Field(default=None, max_length=500)
    overlay_image: str | None = Field(default=None, max_length=500)
    forces: dict | None = None


class CardForeignKeys(SQLModel):
    is_evolution_id: int | None = None
    first_element_id: int | None = None
    second_element_id: int | None = None
    type_id: int | None = None
    character_id: int | None = None
    first_attack_id: int | None = None
    second_attack_id: int | None = None
    ability_id: int | None = None
    association_id: int | None = None

