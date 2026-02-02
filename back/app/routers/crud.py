"""
Generic CRUD Router Factory

Creates standardized CRUD routers from service/schema configuration.
Eliminates duplicate router patterns across simple entities.
"""

from typing import Type, TypeVar

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import SQLModel

from app.database import DBSessionDep
from app.services.base import BaseService
from app.auth.dependencies import get_current_active_user


T = TypeVar("T", bound=SQLModel)  # DB Model
C = TypeVar("C", bound=SQLModel)  # Create schema
R = TypeVar("R", bound=SQLModel)  # Read schema


def create_crud_router(
    *,
    prefix: str,
    tag: str,
    service_class: Type[BaseService],
    read_schema: Type[R],
    create_schema: Type[C],
    entity_name: str,
) -> APIRouter:
    """
    Create a standardized CRUD router for simple entities.
    
    Args:
        prefix: URL prefix (e.g., "/elements")
        tag: OpenAPI tag for grouping
        service_class: Service class inheriting from BaseService
        read_schema: Pydantic schema for read responses
        create_schema: Pydantic schema for create requests
        entity_name: Human-readable entity name for error messages
    
    Returns:
        Configured APIRouter with GET all, GET one, POST, DELETE endpoints
    """
    router = APIRouter(
        prefix=prefix,
        tags=[tag],
        dependencies=[Depends(get_current_active_user)],
    )

    @router.get("", response_model=list[read_schema])
    def get_all(db: DBSessionDep):
        """Get all records."""
        return service_class(db).get_all()

    @router.get("/{value}", response_model=read_schema)
    def get_one(value: str, db: DBSessionDep):
        """Get record by ID or lookup field."""
        result = service_class(db).get(value)
        if not result:
            raise HTTPException(status_code=404, detail=f"{entity_name} not found")
        return result

    @router.post("", response_model=read_schema, status_code=201)
    def create(data: create_schema, db: DBSessionDep):
        """Create a new record."""
        return service_class(db).create(data)

    @router.delete("/{item_id}")
    def delete(item_id: int, db: DBSessionDep):
        """Delete a record by ID."""
        if not service_class(db).delete(item_id):
            raise HTTPException(status_code=404, detail=f"{entity_name} not found")
        return {"message": f"{entity_name} deleted successfully"}

    return router
