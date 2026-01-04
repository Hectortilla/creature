from fastapi import APIRouter, Depends, HTTPException

from app.database import DBSessionDep
from app.models.schemas.ability import AbilityCreate, AbilityRead
from app.services.abilities import AbilityService
from app.auth.dependencies import get_current_active_user

router = APIRouter(
    prefix="/abilities",
    tags=["abilities"],
    dependencies=[Depends(get_current_active_user)],
)


@router.get("", response_model=list[AbilityRead])
def get_all_abilities(db: DBSessionDep):
    """Get all abilities."""
    return AbilityService(db).get_all()


@router.get("/{value}", response_model=AbilityRead)
def get_ability(value: str, db: DBSessionDep):
    """Get ability by code or name."""
    ability = AbilityService(db).get(value)
    if not ability:
        raise HTTPException(status_code=404, detail="Ability not found")
    return ability


@router.post("", response_model=AbilityRead, status_code=201)
def create_ability(ability: AbilityCreate, db: DBSessionDep):
    """Create a new ability."""
    return AbilityService(db).create(ability)


@router.delete("/{ability_id}")
def delete_ability(ability_id: int, db: DBSessionDep):
    """Delete an ability by ID."""
    if not AbilityService(db).delete(ability_id):
        raise HTTPException(status_code=404, detail="Ability not found")
    return {"message": "Ability deleted successfully"}
