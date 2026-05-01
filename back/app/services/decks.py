from sqlmodel import select, Session, func
from fastapi import HTTPException, status
from typing import Optional

from app.models.db.deck import Deck
from app.models.db.card import Card
from app.models.db.deck_card import DeckCard
from app.models.schemas.deck import DeckCreate, DeckUpdate, DeckReadWithCards, DeckReadSummary
from app.models.schemas.card import CardRead, CardReadWithRelations
from app.services.base import BaseService
from app.services.cards import CardService
from app.models.game.state import GameConfiguration


class DeckService(BaseService[Deck, DeckCreate]):
    """Service for Deck CRUD operations."""
    
    model = Deck
    lookup_id_field = "id"
    lookup_str_field = "name"
    has_handle = False
    
    def __init__(self, db: Session, user_id: int):
        super().__init__(db)
        self.user_id = user_id
        self.deck_size = GameConfiguration().deck_size  # 22 cards
    
    def get_user_decks(self) -> list[Deck]:
        """Get all decks for the current user."""
        return self.db.exec(
            select(Deck).where(Deck.user_id == self.user_id)
        ).all()
    
    def get_user_deck(self, deck_id: int) -> Optional[Deck]:
        """Get a specific deck for the current user."""
        deck = self.db.exec(
            select(Deck).where(
                Deck.id == deck_id,
                Deck.user_id == self.user_id
            )
        ).first()
        return deck
    
    def create(self, data: DeckCreate) -> Deck:
        """Create a new deck for the current user."""
        deck = Deck(
            **data.model_dump(),
            user_id=self.user_id
        )
        self.db.add(deck)
        self.db.commit()
        self.db.refresh(deck)
        return deck
    
    def update(self, deck_id: int, data: DeckUpdate) -> Optional[Deck]:
        """Update a deck (only if owned by current user)."""
        deck = self.get_user_deck(deck_id)
        if not deck:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(deck, field, value)
        
        from datetime import datetime
        deck.updated_at = datetime.utcnow()
        
        self.db.add(deck)
        self.db.commit()
        self.db.refresh(deck)
        return deck
    
    def delete(self, deck_id: int) -> bool:
        """Delete a deck (only if owned by current user)."""
        deck = self.get_user_deck(deck_id)
        if not deck:
            return False
        
        # Delete all deck-card associations
        self.db.exec(
            select(DeckCard).where(DeckCard.deck_id == deck_id)
        )
        deck_cards = self.db.exec(
            select(DeckCard).where(DeckCard.deck_id == deck_id)
        ).all()
        for deck_card in deck_cards:
            self.db.delete(deck_card)
        
        self.db.delete(deck)
        self.db.commit()
        return True
    
    def get_deck_card_count(self, deck_id: int) -> int:
        """Get the number of cards in a deck."""
        result = self.db.exec(
            select(func.count(DeckCard.card_id)).where(DeckCard.deck_id == deck_id)
        ).one()
        return result or 0
    
    def add_card_to_deck(self, deck_id: int, card_id: int, position: Optional[int] = None) -> bool:
        """Add a card to a deck."""
        deck = self.get_user_deck(deck_id)
        if not deck:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deck not found"
            )
        
        # Check if card exists
        card = self.db.exec(
            select(Card).where(Card.id == card_id)
        ).first()
        if not card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Card not found"
            )
        
        # Check deck size limit (cards can be repeated, so we just check total count)
        current_count = self.get_deck_card_count(deck_id)
        if current_count >= self.deck_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Deck is full. Maximum {self.deck_size} cards allowed."
            )
        
        # Add card to deck
        deck_card = DeckCard(
            deck_id=deck_id,
            card_id=card_id,
            position=position
        )
        self.db.add(deck_card)
        
        # Update deck updated_at
        from datetime import datetime
        deck.updated_at = datetime.utcnow()
        self.db.add(deck)
        
        self.db.commit()
        return True
    
    def remove_card_from_deck(self, deck_id: int, card_id: int) -> bool:
        """Remove one instance of a card from a deck.
        
        If the same card appears multiple times, only one instance is removed.
        """
        deck = self.get_user_deck(deck_id)
        if not deck:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deck not found"
            )
        
        # Get the first instance of this card in the deck
        deck_card = self.db.exec(
            select(DeckCard).where(
                DeckCard.deck_id == deck_id,
                DeckCard.card_id == card_id
            )
        ).first()
        
        if not deck_card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Card not found in deck"
            )
        
        self.db.delete(deck_card)
        
        # Update deck updated_at
        from datetime import datetime
        deck.updated_at = datetime.utcnow()
        self.db.add(deck)
        
        self.db.commit()
        return True
    
    def enrich(self, deck: Deck) -> DeckReadWithCards:
        """Enrich deck with its cards (including duplicates)."""
        # Query all cards for this deck using a join to preserve duplicates
        # This gets all cards including duplicates by joining through deck_cards
        cards_query = self.db.exec(
            select(Card)
            .join(DeckCard, Card.id == DeckCard.card_id)
            .where(DeckCard.deck_id == deck.id)
            .order_by(DeckCard.id)  # Preserve insertion order
        )
        
        # Enrich each card with full relations for game serialization
        card_service = CardService(self.db)
        cards = [card_service.enrich(card) for card in cards_query.all()]
        
        return DeckReadWithCards(
            id=deck.id,
            user_id=deck.user_id,
            name=deck.name,
            description=deck.description,
            created_at=deck.created_at,
            updated_at=deck.updated_at,
            cards=cards,
        )
    
    def get_all_summaries(self) -> list[DeckReadSummary]:
        """Get all user decks with summary data (lightweight, no card details)."""
        decks = self.get_user_decks()
        summaries = []
        for deck in decks:
            # Count cards without loading them
            card_count = self.get_deck_card_count(deck.id)
            summaries.append(DeckReadSummary(
                id=deck.id,
                user_id=deck.user_id,
                name=deck.name,
                description=deck.description,
                created_at=deck.created_at,
                updated_at=deck.updated_at,
                card_count=card_count,
            ))
        return summaries
    
    def get_all_enriched(self) -> list[DeckReadWithCards]:
        """Get all user decks with enriched data."""
        decks = self.get_user_decks()
        return [self.enrich(deck) for deck in decks]
    
    def get_enriched(self, deck_id: int) -> Optional[DeckReadWithCards]:
        """Get a specific deck with enriched data."""
        deck = self.get_user_deck(deck_id)
        if not deck:
            return None
        return self.enrich(deck)

