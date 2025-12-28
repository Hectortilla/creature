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
from app.models.schemas.websocket import *

# Import models to ensure they're registered with SQLModel
from app.models.db import (
    Element, Type, Character, Attack, Ability, Association, Card, User, Deck, DeckCard
)
from app.settings.lifespan import lifespan

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
# WebSocket Message Type Definitions (for TypeScript generation)
# ============================================================================

# Client → Server Messages
@app.post("/websocket-messages/create-game", response_model=CreateGameMessage, tags=["WebSocket Messages"], include_in_schema=True)
async def _ws_create_game_type(msg: CreateGameMessage) -> CreateGameMessage:
    """WebSocket message type: create_game (dummy endpoint for type generation)."""
    return msg

@app.post("/websocket-messages/join-game", response_model=JoinGameMessage, tags=["WebSocket Messages"], include_in_schema=True)
async def _ws_join_game_type(msg: JoinGameMessage) -> JoinGameMessage:
    """WebSocket message type: join_game (dummy endpoint for type generation)."""
    return msg

@app.post("/websocket-messages/list-rooms", response_model=ListRoomsMessage, tags=["WebSocket Messages"], include_in_schema=True)
async def _ws_list_rooms_type(msg: ListRoomsMessage) -> ListRoomsMessage:
    """WebSocket message type: list_rooms (dummy endpoint for type generation)."""
    return msg

@app.post("/websocket-messages/start-game", response_model=StartGameMessage, tags=["WebSocket Messages"], include_in_schema=True)
async def _ws_start_game_type(msg: StartGameMessage) -> StartGameMessage:
    """WebSocket message type: start_game (dummy endpoint for type generation)."""
    return msg

@app.post("/websocket-messages/action", response_model=ActionMessage, tags=["WebSocket Messages"], include_in_schema=True)
async def _ws_action_type(msg: ActionMessage) -> ActionMessage:
    """WebSocket message type: action (dummy endpoint for type generation)."""
    return msg

@app.post("/websocket-messages/get-state", response_model=GetStateMessage, tags=["WebSocket Messages"], include_in_schema=True)
async def _ws_get_state_type(msg: GetStateMessage) -> GetStateMessage:
    """WebSocket message type: get_state (dummy endpoint for type generation)."""
    return msg

@app.post("/websocket-messages/get-valid-actions", response_model=GetValidActionsMessage, tags=["WebSocket Messages"], include_in_schema=True)
async def _ws_get_valid_actions_type(msg: GetValidActionsMessage) -> GetValidActionsMessage:
    """WebSocket message type: get_valid_actions (dummy endpoint for type generation)."""
    return msg

@app.post("/websocket-messages/leave-game", response_model=LeaveGameMessage, tags=["WebSocket Messages"], include_in_schema=True)
async def _ws_leave_game_type(msg: LeaveGameMessage) -> LeaveGameMessage:
    """WebSocket message type: leave_game (dummy endpoint for type generation)."""
    return msg

@app.post("/websocket-messages/ping", response_model=PingMessage, tags=["WebSocket Messages"], include_in_schema=True)
async def _ws_ping_type(msg: PingMessage) -> PingMessage:
    """WebSocket message type: ping (dummy endpoint for type generation)."""
    return msg

# Server → Client Messages (return types)
@app.get("/websocket-messages/connected", response_model=ConnectedMessage, tags=["WebSocket Messages"], include_in_schema=True)
async def _ws_connected_type() -> ConnectedMessage:
    """WebSocket message type: connected (dummy endpoint for type generation)."""
    return ConnectedMessage()

@app.get("/websocket-messages/game-created", response_model=GameCreatedMessage, tags=["WebSocket Messages"], include_in_schema=True)
async def _ws_game_created_type() -> GameCreatedMessage:
    """WebSocket message type: game_created (dummy endpoint for type generation)."""
    return GameCreatedMessage()

@app.get("/websocket-messages/game-joined", response_model=GameJoinedMessage, tags=["WebSocket Messages"], include_in_schema=True)
async def _ws_game_joined_type() -> GameJoinedMessage:
    """WebSocket message type: game_joined (dummy endpoint for type generation)."""
    return GameJoinedMessage()

@app.get("/websocket-messages/player-joined", response_model=PlayerJoinedMessage, tags=["WebSocket Messages"], include_in_schema=True)
async def _ws_player_joined_type() -> PlayerJoinedMessage:
    """WebSocket message type: player_joined (dummy endpoint for type generation)."""
    return PlayerJoinedMessage()

@app.get("/websocket-messages/player-left", response_model=PlayerLeftMessage, tags=["WebSocket Messages"], include_in_schema=True)
async def _ws_player_left_type() -> PlayerLeftMessage:
    """WebSocket message type: player_left (dummy endpoint for type generation)."""
    return PlayerLeftMessage()

@app.get("/websocket-messages/game-started", response_model=GameStartedMessage, tags=["WebSocket Messages"], include_in_schema=True)
async def _ws_game_started_type() -> GameStartedMessage:
    """WebSocket message type: game_started (dummy endpoint for type generation)."""
    return GameStartedMessage()

@app.get("/websocket-messages/game-state", response_model=GameStateMessage, tags=["WebSocket Messages"], include_in_schema=True)
async def _ws_game_state_type() -> GameStateMessage:
    """WebSocket message type: game_state (dummy endpoint for type generation)."""
    return GameStateMessage()

@app.get("/websocket-messages/action-result", response_model=ActionResultMessage, tags=["WebSocket Messages"], include_in_schema=True)
async def _ws_action_result_type() -> ActionResultMessage:
    """WebSocket message type: action_result (dummy endpoint for type generation)."""
    return ActionResultMessage()

@app.get("/websocket-messages/valid-actions", response_model=ValidActionsMessage, tags=["WebSocket Messages"], include_in_schema=True)
async def _ws_valid_actions_type() -> ValidActionsMessage:
    """WebSocket message type: valid_actions (dummy endpoint for type generation)."""
    return ValidActionsMessage()

@app.get("/websocket-messages/rooms-list", response_model=RoomsListMessage, tags=["WebSocket Messages"], include_in_schema=True)
async def _ws_rooms_list_type() -> RoomsListMessage:
    """WebSocket message type: rooms_list (dummy endpoint for type generation)."""
    return RoomsListMessage()

@app.get("/websocket-messages/game-left", response_model=GameLeftMessage, tags=["WebSocket Messages"], include_in_schema=True)
async def _ws_game_left_type() -> GameLeftMessage:
    """WebSocket message type: game_left (dummy endpoint for type generation)."""
    return GameLeftMessage()

@app.get("/websocket-messages/error", response_model=ErrorMessage, tags=["WebSocket Messages"], include_in_schema=True)
async def _ws_error_type() -> ErrorMessage:
    """WebSocket message type: error (dummy endpoint for type generation)."""
    return ErrorMessage()

@app.get("/websocket-messages/pong", response_model=PongMessage, tags=["WebSocket Messages"], include_in_schema=True)
async def _ws_pong_type() -> PongMessage:
    """WebSocket message type: pong (dummy endpoint for type generation)."""
    return PongMessage()


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
        from app.settings.lifespan import game_manager as gm
        if gm and player_id in gm.connections:
            existing_connection = gm.connections[player_id]
            if existing_connection.game_id:
                # Check if the game is still active
                room = gm.get_room(existing_connection.game_id)
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
    # Import here to ensure game_manager is initialized from lifespan
    from app.settings.lifespan import game_manager as gm
    if gm is None:
        raise WebSocketException(
            code=status.WS_1011_INTERNAL_ERROR,
            reason="Game manager not initialized",
        )
    await game_websocket_handler(websocket, player_id, name, gm, serialized_deck)


@app.get("/game/rooms")
async def list_game_rooms():
    """
    List all available game rooms (HTTP endpoint for convenience).
    
    Returns rooms that haven't started yet.
    """
    from app.settings.lifespan import game_manager as gm
    if gm is None:
        return {"rooms": []}
    return {"rooms": gm.list_rooms()}
