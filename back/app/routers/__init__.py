"""
Router Registration

Configures and exports all API routers.
Simple CRUD entities use the factory pattern.
"""

from app.models.schemas.ability import AbilityCreate, AbilityRead
from app.models.schemas.association import AssociationCreate, AssociationRead
from app.models.schemas.character import CharacterCreate, CharacterRead

# Schemas
from app.models.schemas.element import ElementCreate, ElementRead
from app.models.schemas.type import TypeCreate, TypeRead
from app.routers.crud import create_crud_router

# Services (simple services now defined in base.py)
from app.services.base import (
    AbilityService,
    AssociationService,
    CharacterService,
    ElementService,
    TypeService,
)

# Generate CRUD routers using factory
elements_router = create_crud_router(
    prefix="/elements",
    tag="elements",
    service_class=ElementService,
    read_schema=ElementRead,
    create_schema=ElementCreate,
    entity_name="Element",
)

types_router = create_crud_router(
    prefix="/types",
    tag="types",
    service_class=TypeService,
    read_schema=TypeRead,
    create_schema=TypeCreate,
    entity_name="Type",
)

abilities_router = create_crud_router(
    prefix="/abilities",
    tag="abilities",
    service_class=AbilityService,
    read_schema=AbilityRead,
    create_schema=AbilityCreate,
    entity_name="Ability",
)

characters_router = create_crud_router(
    prefix="/characters",
    tag="characters",
    service_class=CharacterService,
    read_schema=CharacterRead,
    create_schema=CharacterCreate,
    entity_name="Character",
)

associations_router = create_crud_router(
    prefix="/associations",
    tag="associations",
    service_class=AssociationService,
    read_schema=AssociationRead,
    create_schema=AssociationCreate,
    entity_name="Association",
)

# Custom routers (not using factory - have additional endpoints)
from app.routers.attacks import router as attacks_router
from app.routers.auth import router as auth_router
from app.routers.cards import router as cards_router
from app.routers.decks import router as decks_router
