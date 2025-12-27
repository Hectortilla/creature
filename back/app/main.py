"""
Creature Card Game API

Main FastAPI application with WebSocket-based game system.
"""

from broadcaster import Broadcast
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.settings.config import get_settings
from app.database import create_db_and_tables
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
from app.websocket import GameManager, game_websocket_handler
from app.auth import WebSocketUser

# Import models to ensure they're registered with SQLModel
from app.models.db import (
    Element, Type, Character, Attack, Ability, Association, Card, User, Deck, DeckCard
)
from app.settings.lifespan import lifespan
from app.settings.lifespan import game_manager

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

# Include auth router
app.include_router(auth_router)

# Include data routers (cards, attacks, etc.)
app.include_router(elements_router)
app.include_router(types_router)
app.include_router(characters_router)
app.include_router(attacks_router)
app.include_router(abilities_router)
app.include_router(associations_router)
app.include_router(cards_router)
app.include_router(decks_router)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Creature Card Game API", "status": "healthy"}


# ============================================================================
# Game WebSocket Endpoint
# ============================================================================

@app.websocket("/game/ws")
async def game_websocket(
    websocket: WebSocket,
    user: WebSocketUser,
):
    """
    Authenticated WebSocket endpoint for game connections.
    
    Connect with: ws://host/game/ws?token=<jwt_token>
    
    Player ID is the user's database ID, name is the user's full_name or username.
    """
    player_id = str(user.id)
    name = user.full_name or user.username
    await game_websocket_handler(websocket, player_id, name, game_manager)


@app.get("/game/rooms")
async def list_game_rooms():
    """
    List all available game rooms (HTTP endpoint for convenience).
    
    Returns rooms that haven't started yet.
    """
    if game_manager is None:
        return {"rooms": []}
    return {"rooms": game_manager.list_rooms()}
