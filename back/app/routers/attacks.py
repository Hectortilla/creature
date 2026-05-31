from fastapi import APIRouter, Depends, HTTPException

from app.auth.dependencies import get_current_active_user
from app.database import DBSessionDep
from app.models.schemas.attack import AttackCreate, AttackReadWithElement
from app.services.attacks import AttackService

router = APIRouter(
    prefix="/attacks",
    tags=["attacks"],
    dependencies=[Depends(get_current_active_user)],
)


@router.get("", response_model=list[AttackReadWithElement])
def get_all_attacks(db: DBSessionDep):
    """Get all attacks with enriched data."""
    return AttackService(db).get_all_enriched()


@router.get("/{value}", response_model=AttackReadWithElement)
def get_attack(value: str, db: DBSessionDep):
    """Get attack by code or name."""
    attack = AttackService(db).get_enriched(value)
    if not attack:
        raise HTTPException(status_code=404, detail="Attack not found")
    return attack


@router.post("", response_model=AttackReadWithElement, status_code=201)
def create_attack(attack: AttackCreate, db: DBSessionDep):
    """Create a new attack."""
    service = AttackService(db)
    db_attack = service.create(attack)
    return service.enrich(db_attack)


@router.delete("/{attack_id}")
def delete_attack(attack_id: int, db: DBSessionDep):
    """Delete an attack by ID."""
    if not AttackService(db).delete(attack_id):
        raise HTTPException(status_code=404, detail="Attack not found")
    return {"message": "Attack deleted successfully"}
