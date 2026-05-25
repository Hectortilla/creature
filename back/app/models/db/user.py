from sqlmodel import Field, Relationship, SQLModel, Session
from datetime import datetime
from typing import TYPE_CHECKING

from app.models.base.user import UserBase

if TYPE_CHECKING:
    from app.models.db.card import Card
    from app.models.db.deck import Deck
    from app.models.game.player import PlayerState
    
    
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
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    decks: list["Deck"] = Relationship(back_populates="user")
    cards: list["Card"] = Relationship(
        back_populates="users", 
        link_model=UserCard,  
        sa_relationship_kwargs={"lazy": "selectin"}
    )
    
    def to_player_state(self, deck_id: int, db: Session) -> "PlayerState":
        """
        Create a PlayerState from this user with the given deck.
        
        Fetches, validates, enriches, and serializes the deck.
        
        Args:
            deck_id: The ID of the deck to use
            db: Database session
            
        Returns:
            PlayerState with the serialized deck
            
        Raises:
            ValueError: If deck is not found, doesn't belong to user, or is invalid
        """
        from app.models.game.player import PlayerState
        from app.services.decks import DeckService
        from app.websocket.serialization import serialize_deck_for_game
        
        # Get and validate deck
        deck_service = DeckService(db, self.id)
        deck = deck_service.get_user_deck(deck_id)
        
        if not deck:
            raise ValueError("Deck not found or does not belong to user")
        
        # Validate deck is valid for playing
        if not deck.is_valid_for_playing(db):
            raise ValueError("Deck is not valid for playing")
        
        # Serialize deck
        enriched_deck = deck_service.get_enriched(deck_id)
        if not enriched_deck:
            raise ValueError("Failed to load deck")
        
        serialized_deck = serialize_deck_for_game(enriched_deck.cards)
        
        return PlayerState(
            player_id=str(self.id),
            name=self.full_name or self.username,
            deck=serialized_deck
        )
