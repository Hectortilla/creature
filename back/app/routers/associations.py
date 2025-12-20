from fastapi import APIRouter, HTTPException

from app.database import DBSessionDep
from app.models.schemas import AssociationCreate, AssociationRead
from app.services import AssociationService

router = APIRouter(prefix="/associations", tags=["associations"])


@router.get("", response_model=list[AssociationRead])
def get_all_associations(db: DBSessionDep):
    """Get all associations."""
    return AssociationService(db).get_all()


@router.get("/{value}", response_model=AssociationRead)
def get_association(value: str, db: DBSessionDep):
    """Get association by code or name."""
    association = AssociationService(db).get(value)
    if not association:
        raise HTTPException(status_code=404, detail="Association not found")
    return association


@router.post("", response_model=AssociationRead, status_code=201)
def create_association(association: AssociationCreate, db: DBSessionDep):
    """Create a new association."""
    return AssociationService(db).create(association)


@router.delete("/{association_id}")
def delete_association(association_id: int, db: DBSessionDep):
    """Delete an association by ID."""
    if not AssociationService(db).delete(association_id):
        raise HTTPException(status_code=404, detail="Association not found")
    return {"message": "Association deleted successfully"}
