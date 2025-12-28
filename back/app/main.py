"""
Creature Card Game API

Main FastAPI application with WebSocket-based game system.
"""

from broadcaster import Broadcast
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, Depends, Request, status, WebSocketException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.settings.config import get_settings
from app.database import create_db_and_tables, get_db_session
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
from app.websocket import GameManager, game_websocket_handler, serialize_deck_for_game
from app.auth import WebSocketUser
from app.services.decks import DeckService
from app.models.game.enums import GameStatus

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
    deck_id: int = Query(..., description="Deck ID to use for the game"),
):
    """
    Authenticated WebSocket endpoint for game connections.
    
    Connect with: ws://host/game/ws?token=<jwt_token>&deck_id=<deck_id>
    
    Player ID is the user's database ID, name is the user's full_name or username.
    
    Validates:
    - Deck exists and belongs to the user
    - Deck is valid for playing (correct size)
    - Player doesn't have another active game
    """
    player_id = str(user.id)
    name = user.full_name or user.username
    
    # Get database session
    db = next(get_db_session())
    try:
        # Check if player already has an active game
        if game_manager and player_id in game_manager.connections:
            existing_connection = game_manager.connections[player_id]
            if existing_connection.game_id:
                # Check if the game is still active
                room = game_manager.get_room(existing_connection.game_id)
                if room:
                    # If game has started and is not finished, refuse connection
                    if room.state and room.state.status != GameStatus.FINISHED:
                        raise WebSocketException(
                            code=status.WS_1008_POLICY_VIOLATION,
                            reason="Player already has an active game",
                        )
                    # If game hasn't started but room exists, also refuse (player is in a waiting room)
                    elif not room.state:
                        raise WebSocketException(
                            code=status.WS_1008_POLICY_VIOLATION,
                            reason="Player already has an active game",
                        )
        
        # Get and validate deck
        deck_service = DeckService(db, user.id)
        deck = deck_service.get_user_deck(deck_id)
        
        if not deck:
            raise WebSocketException(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="Deck not found or does not belong to user",
            )
        
        # Validate deck is valid for playing
        if not deck.is_valid_for_playing(db):
            raise WebSocketException(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="Deck is not valid for playing",
            )
        
        # Serialize deck
        enriched_deck = deck_service.get_enriched(deck_id)
        if not enriched_deck:
            raise WebSocketException(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="Failed to load deck",
            )
        
        serialized_deck = serialize_deck_for_game(enriched_deck.cards)
        
    finally:
        db.close()
    
    # Pass serialized deck to handler
    await game_websocket_handler(websocket, player_id, name, game_manager, serialized_deck)


@app.get("/game/rooms")
async def list_game_rooms():
    """
    List all available game rooms (HTTP endpoint for convenience).
    
    Returns rooms that haven't started yet.
    """
    if game_manager is None:
        return {"rooms": []}
    return {"rooms": game_manager.list_rooms()}
