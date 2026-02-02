from fastapi import APIRouter, Depends, HTTPException

from app.database import DBSessionDep
from app.models.schemas.card import CardCreate, CardReadWithRelations
from app.services.cards import CardService
from app.auth.dependencies import get_current_active_user

router = APIRouter(
    prefix="/cards",
    tags=["cards"],
    dependencies=[Depends(get_current_active_user)],
)


@router.get("", response_model=list[CardReadWithRelations])
def get_all_cards(db: DBSessionDep):
    """Get all cards with enriched data."""
    return CardService(db).get_all_enriched()


@router.get("/{value}", response_model=list[CardReadWithRelations])
def get_card(value: str, db: DBSessionDep):
    """Get card by code, handle, or name."""
    cards = CardService(db).get_enriched(value)
    if not cards:
        raise HTTPException(status_code=404, detail="Card not found")
    return cards


@router.get("/by-attack/{attack_code}", response_model=list[CardReadWithRelations])
def get_cards_by_attack(attack_code: int, db: DBSessionDep):
    """Get all cards that have a specific attack."""
    return CardService(db).get_by_attack(attack_code)


@router.get("/by-ability/{ability_code}", response_model=list[CardReadWithRelations])
def get_cards_by_ability(ability_code: int, db: DBSessionDep):
    """Get all cards that have a specific ability."""
    return CardService(db).get_by_ability(ability_code)


@router.get("/by-association/{association_code}", response_model=list[CardReadWithRelations])
def get_cards_by_association(association_code: int, db: DBSessionDep):
    """Get all cards that have a specific association."""
    return CardService(db).get_by_association(association_code)


@router.post("", response_model=CardReadWithRelations, status_code=201)
def create_card(card: CardCreate, db: DBSessionDep):
    """Create a new card."""
    service = CardService(db)
    db_card = service.create(card)
    return service.enrich(db_card)


@router.delete("/{card_id}")
def delete_card(card_id: int, db: DBSessionDep):
    """Delete a card by ID."""
    if not CardService(db).delete(card_id):
        raise HTTPException(status_code=404, detail="Card not found")
    return {"message": "Card deleted successfully"}
