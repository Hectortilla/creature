from fastapi import APIRouter, HTTPException

from app.database import DBSessionDep
from app.models.schemas import ElementCreate, ElementRead
from app.services import ElementService

router = APIRouter(prefix="/elements", tags=["elements"])


@router.get("", response_model=list[ElementRead])
def get_all_elements(db: DBSessionDep):
    """Get all elements."""
    return ElementService(db).get_all()


@router.get("/{value}", response_model=ElementRead)
def get_element(value: str, db: DBSessionDep):
    """Get element by ID or label."""
    element = ElementService(db).get(value)
    if not element:
        raise HTTPException(status_code=404, detail="Element not found")
    return element


@router.post("", response_model=ElementRead, status_code=201)
def create_element(element: ElementCreate, db: DBSessionDep):
    """Create a new element."""
    return ElementService(db).create(element)


@router.delete("/{element_id}")
def delete_element(element_id: int, db: DBSessionDep):
    """Delete an element by ID."""
    if not ElementService(db).delete(element_id):
        raise HTTPException(status_code=404, detail="Element not found")
    return {"message": "Element deleted successfully"}
