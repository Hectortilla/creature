from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from app.models.base.user import UserBase
from app.utils.time import utcnow

if TYPE_CHECKING:
    from app.models.db.card import Card
    from app.models.db.deck import Deck


class UserCard(SQLModel, table=True):
    __tablename__ = "user_cards"

    user_id: int | None = Field(default=None, foreign_key="users.id", primary_key=True)
    card_id: int | None = Field(default=None, foreign_key="cards.id", primary_key=True)

    # Campos adicionales en el futuro:
    # como 'quantity' (si puede tener copias de la misma carta), 'foil' (si es brillante), etc.
    quantity: int = Field(default=1)


class User(UserBase, table=True):
    """User database model."""

    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True, max_length=50)
    email: str | None = Field(default=None, unique=True, index=True, max_length=255)
    hashed_password: str = Field(max_length=255)
    created_at: datetime = Field(default_factory=utcnow)

    # Relationships
    decks: list["Deck"] = Relationship(back_populates="user")
    cards: list["Card"] = Relationship(
        back_populates="users", link_model=UserCard, sa_relationship_kwargs={"lazy": "selectin"}
    )
