from sqlmodel import Field, Relationship, Column
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from app.models.base.card import CardBase, CardForeignKeys

if TYPE_CHECKING:
    from app.models.db.element import Element
    from app.models.db.type import Type
    from app.models.db.character import Character
    from app.models.db.attack import Attack
    from app.models.db.ability import Ability
    from app.models.db.association import Association
    from app.models.db.deck import Deck
    from app.models.db import DeckCard
else:
    from app.models.db.deck_card import DeckCard


class Card(CardBase, CardForeignKeys, table=True):
    __tablename__ = "cards"
    
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    code: int = Field(unique=True)
    handle: str = Field(default="", max_length=255)
    forces: dict | None = Field(default=None, sa_column=Column(JSONB))
    
    # Foreign keys with constraints
    is_evolution_id: int | None = Field(default=None, foreign_key="cards.id")
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
    
    # Many-to-many relationship with decks
    decks: list["Deck"] = Relationship(
        back_populates="cards",
        link_model=DeckCard,
        sa_relationship_kwargs={"lazy": "selectin"}
    )
