from sqlmodel import SQLModel, Field


class CardBase(SQLModel):
    code: int
    name: str = Field(max_length=255)
    description: str | None = None
    image: str | None = Field(default=None, max_length=500)
    overlay_image: str | None = Field(default=None, max_length=500)
    health: int | None = None
    physical_defence: int | None = None
    magic_defence: int | None = None
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

