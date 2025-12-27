"""
Creature Card Game API

Main FastAPI application with WebSocket-based game system.
"""

from broadcaster import Broadcast
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware

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
)
from app.game.websocket import GameManager, game_websocket_handler

# Import models to ensure they're registered with SQLModel
from app.models.db import (
    Element, Type, Character, Attack, Ability, Association, Card
)
from app.settings.lifespan import lifespan
from app.settings.lifespan import game_manager

app = FastAPI(
    title="Creature Card Game API",
    description="API for managing creature cards, attacks, abilities, and real-time game play",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include data routers (cards, attacks, etc.)
app.include_router(elements_router)
app.include_router(types_router)
app.include_router(characters_router)
app.include_router(attacks_router)
app.include_router(abilities_router)
app.include_router(associations_router)
app.include_router(cards_router)


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
    player_id: str = Query(..., description="Unique player identifier"),
    name: str = Query("Player", description="Player display name"),
):
    """
    WebSocket endpoint for real-time game communication.
    
    Connect with: ws://host/game/ws?player_id=YOUR_ID&name=YOUR_NAME
    
    Message Protocol (send JSON):
    
    ## Create a new game room:
    ```json
    {
        "type": "create_game",
        "data": {
            "name": "Player Name",
            "deck": [{"id": 1, "name": "Card 1", ...}, ...]
        }
    }
    ```
    
    ## List available rooms:
    ```json
    {"type": "list_rooms"}
    ```
    
    ## Join an existing room:
    ```json
    {
        "type": "join_game",
        "data": {
            "room_id": "room-uuid",
            "name": "Player Name", 
            "deck": [...]
        }
    }
    ```
    
    ## Start the game (host only):
    ```json
    {"type": "start_game"}
    ```
    
    ## Perform a game action:
    ```json
    {
        "type": "action",
        "data": {
            "action_type": "play_card",
            "card_id": "card-instance-id"
        }
    }
    ```
    
    ## Get current game state:
    ```json
    {"type": "get_state"}
    ```
    
    ## Get valid actions:
    ```json
    {"type": "get_valid_actions"}
    ```
    
    ## Leave current game:
    ```json
    {"type": "leave_game"}
    ```
    
    ## Keep-alive ping:
    ```json
    {"type": "ping"}
    ```
    """
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
