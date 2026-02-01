"""
Creature Card Game API

Main FastAPI application entrypoint.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
    elements_router,
    types_router,
    characters_router,
    attacks_router,
    abilities_router,
    associations_router,
    cards_router,
    auth_router,
    decks_router,
)
from app.websocket.router import router as websocket_router
from app.settings.lifespan import lifespan

# Import models to ensure they're registered with SQLModel
from app.models.db.element import Element
from app.models.db.type import Type
from app.models.db.character import Character
from app.models.db.attack import Attack
from app.models.db.ability import Ability
from app.models.db.association import Association
from app.models.db.card import Card
from app.models.db.user import User
from app.models.db.deck import Deck
from app.models.db.deck_card import DeckCard

app = FastAPI(
    title="Creature Card Game API",
    description="API for managing creature cards, attacks, abilities, and real-time game play",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(elements_router)
app.include_router(types_router)
app.include_router(characters_router)
app.include_router(attacks_router)
app.include_router(abilities_router)
app.include_router(associations_router)
app.include_router(cards_router)
app.include_router(decks_router)
app.include_router(websocket_router, prefix="/game", tags=["Game"])


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Creature Card Game API", "status": "healthy"}
