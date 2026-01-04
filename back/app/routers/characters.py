from fastapi import APIRouter, Depends, HTTPException

from app.database import DBSessionDep
from app.models.schemas.character import CharacterCreate, CharacterRead
from app.services.characters import CharacterService
from app.auth.dependencies import get_current_active_user

router = APIRouter(
    prefix="/characters",
    tags=["characters"],
    dependencies=[Depends(get_current_active_user)],
)


@router.get("", response_model=list[CharacterRead])
def get_all_characters(db: DBSessionDep):
    """Get all characters."""
    return CharacterService(db).get_all()


@router.get("/{value}", response_model=CharacterRead)
def get_character(value: str, db: DBSessionDep):
    """Get character by ID or label."""
    character = CharacterService(db).get(value)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return character


@router.post("", response_model=CharacterRead, status_code=201)
def create_character(character: CharacterCreate, db: DBSessionDep):
    """Create a new character."""
    return CharacterService(db).create(character)


@router.delete("/{character_id}")
def delete_character(character_id: int, db: DBSessionDep):
    """Delete a character by ID."""
    if not CharacterService(db).delete(character_id):
        raise HTTPException(status_code=404, detail="Character not found")
    return {"message": "Character deleted successfully"}
