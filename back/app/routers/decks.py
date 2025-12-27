from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from typing import List

from app.database import DBSessionDep
from app.models.schemas import DeckCreate, DeckUpdate, DeckRead, DeckReadWithCards
from app.services.decks import DeckService
from app.auth import get_current_active_user, CurrentActiveUser
from app.models.db import User

router = APIRouter(
    prefix="/decks",
    tags=["decks"],
    dependencies=[Depends(get_current_active_user)],
)


@router.get("", response_model=List[DeckReadWithCards])
def get_all_decks(
    db: DBSessionDep,
    current_user: CurrentActiveUser,
):
    """Get all decks for the current user."""
    return DeckService(db, current_user.id).get_all_enriched()


@router.get("/{deck_id}", response_model=DeckReadWithCards)
def get_deck(
    deck_id: int,
    db: DBSessionDep,
    current_user: CurrentActiveUser,
):
    """Get a specific deck by ID (only if owned by current user)."""
    deck = DeckService(db, current_user.id).get_enriched(deck_id)
    if not deck:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found"
        )
    return deck


@router.post("", response_model=DeckReadWithCards, status_code=status.HTTP_201_CREATED)
def create_deck(
    deck: DeckCreate,
    db: DBSessionDep,
    current_user: CurrentActiveUser,
):
    """Create a new deck for the current user."""
    service = DeckService(db, current_user.id)
    db_deck = service.create(deck)
    return service.enrich(db_deck)


@router.put("/{deck_id}", response_model=DeckReadWithCards)
def update_deck(
    deck_id: int,
    deck_update: DeckUpdate,
    db: DBSessionDep,
    current_user: CurrentActiveUser,
):
    """Update a deck (only if owned by current user)."""
    service = DeckService(db, current_user.id)
    updated_deck = service.update(deck_id, deck_update)
    if not updated_deck:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found"
        )
    return service.enrich(updated_deck)


@router.delete("/{deck_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_deck(
    deck_id: int,
    db: DBSessionDep,
    current_user: CurrentActiveUser,
):
    """Delete a deck (only if owned by current user)."""
    if not DeckService(db, current_user.id).delete(deck_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found"
        )


@router.post("/{deck_id}/cards/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def add_card_to_deck(
    deck_id: int,
    card_id: int,
    db: DBSessionDep,
    current_user: CurrentActiveUser,
):
    """Add a card to a deck."""
    DeckService(db, current_user.id).add_card_to_deck(deck_id, card_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/{deck_id}/cards/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_card_from_deck(
    deck_id: int,
    card_id: int,
    db: DBSessionDep,
    current_user: CurrentActiveUser,
):
    """Remove a card from a deck."""
    DeckService(db, current_user.id).remove_card_from_deck(deck_id, card_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

