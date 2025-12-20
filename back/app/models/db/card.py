from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from app.models.db.element import Element
    from app.models.db.type import Type
    from app.models.db.character import Character
    from app.models.db.attack import Attack
    from app.models.db.ability import Ability
    from app.models.db.association import Association


class Card(SQLModel, table=True):
    __tablename__ = "cards"
    
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    code: int = Field(unique=True)
    name: str = Field(max_length=255)
    handle: str = Field(default="", max_length=255)
    description: str | None = Field(default=None)
    image: str | None = Field(default=None, max_length=500)
    overlay_image: str | None = Field(default=None, max_length=500)
    health: int | None = Field(default=None)
    physical_defence: int | None = Field(default=None)
    magic_defence: int | None = Field(default=None)
    forces: dict | None = Field(default=None, sa_column=Column(JSONB))
    
    # Evolution reference (self-referential)
    is_evolution_id: int | None = Field(default=None, foreign_key="cards.id")
    
    # Foreign keys
    first_element_id: int | None = Field(default=None, foreign_key="elements.id")
    second_element_id: int | None = Field(default=None, foreign_key="elements.id")
    type_id: int | None = Field(default=None, foreign_key="types.id")
    character_id: int | None = Field(default=None, foreign_key="characters.id")
    first_attack_id: int | None = Field(default=None, foreign_key="attacks.id")
    second_attack_id: int | None = Field(default=None, foreign_key="attacks.id")
    ability_id: int | None = Field(default=None, foreign_key="abilities.id")
    association_id: int | None = Field(default=None, foreign_key="associations.id")
    
    # Relationships
    first_element: Optional["Element"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Card.first_element_id]"}
    )
    second_element: Optional["Element"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Card.second_element_id]"}
    )
    type: Optional["Type"] = Relationship()
    character: Optional["Character"] = Relationship()
    first_attack: Optional["Attack"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Card.first_attack_id]"}
    )
    second_attack: Optional["Attack"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Card.second_attack_id]"}
    )
    ability: Optional["Ability"] = Relationship()
    association: Optional["Association"] = Relationship()
    
    # Self-referential relationship for evolution
    is_evolution: Optional["Card"] = Relationship(
        sa_relationship_kwargs={"remote_side": "Card.id", "foreign_keys": "[Card.is_evolution_id]"}
    )

