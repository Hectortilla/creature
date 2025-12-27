from sqlmodel import Field, Relationship
from datetime import datetime
from typing import TYPE_CHECKING

from app.models.base.user import UserBase

if TYPE_CHECKING:
    from app.models.db.deck import Deck


class User(UserBase, table=True):
    """User database model."""
    __tablename__ = "users"
    
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True, max_length=50)
    email: str | None = Field(default=None, unique=True, index=True, max_length=255)
    hashed_password: str = Field(max_length=255)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    decks: list["Deck"] = Relationship(back_populates="user")
