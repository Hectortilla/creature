from fastapi import APIRouter, Depends, HTTPException

from app.database import DBSessionDep
from app.models.schemas.type import TypeCreate, TypeRead
from app.services.types import TypeService
from app.auth.dependencies import get_current_active_user

router = APIRouter(
    prefix="/types",
    tags=["types"],
    dependencies=[Depends(get_current_active_user)],
)


@router.get("", response_model=list[TypeRead])
def get_all_types(db: DBSessionDep):
    """Get all types."""
    return TypeService(db).get_all()


@router.get("/{value}", response_model=TypeRead)
def get_type(value: str, db: DBSessionDep):
    """Get type by ID or label."""
    type_obj = TypeService(db).get(value)
    if not type_obj:
        raise HTTPException(status_code=404, detail="Type not found")
    return type_obj


@router.post("", response_model=TypeRead, status_code=201)
def create_type(type_data: TypeCreate, db: DBSessionDep):
    """Create a new type."""
    return TypeService(db).create(type_data)


@router.delete("/{type_id}")
def delete_type(type_id: int, db: DBSessionDep):
    """Delete a type by ID."""
    if not TypeService(db).delete(type_id):
        raise HTTPException(status_code=404, detail="Type not found")
    return {"message": "Type deleted successfully"}
