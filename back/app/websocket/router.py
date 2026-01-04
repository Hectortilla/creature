"""
WebSocket Router

FastAPI router for WebSocket and HTTP endpoints related to game connections.
"""
import traceback
from fastapi import APIRouter, WebSocket, Query, status, WebSocketException

from app.auth.dependencies import WebSocketUser
from app.models.schemas.websocket.client import (
    JoinGameMessage,
    ListRoomsMessage,
    ActionMessage,
    GetStateMessage,
    GetValidActionsMessage,
    LeaveGameMessage,
    PingMessage,
)
from app.models.schemas.websocket.server import (
    ConnectedMessage,
    GameCreatedMessage,
    GameJoinedMessage,
    PlayerJoinedMessage,
    PlayerLeftMessage,
    GameStartedMessage,
    GameStateMessage,
    ActionResultMessage,
    ValidActionsMessage,
    RoomsListMessage,
    GameLeftMessage,
    ErrorMessage,
    PongMessage,
)
from app.websocket import game_websocket_handler
from app.database import get_db_session

router = APIRouter()


@router.websocket("/ws")
async def game_websocket(
    websocket: WebSocket,
    user: WebSocketUser,
    deck_id: int = Query(..., description="Deck ID to use for the game"),
    room_id: str = Query(None, description="Optional room ID to join an existing room"),
):
    """
    Authenticated WebSocket endpoint for game connections.
    
    Connect with: ws://host/game/ws?token=<jwt_token>&deck_id=<deck_id>[&room_id=<room_id>]
    
    If room_id is provided, the player will automatically join that room after connecting.
    If room_id is not provided, the player will need to create or join a room via messages.
    """

    try:
        db = next(get_db_session())
        player = user.to_player_state(deck_id, db)
    except Exception as e:
        db.close()
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason=traceback.format_exc(),
        )
    finally:
        db.close()

    await game_websocket_handler(
        websocket, 
        player,
        room_id=room_id
    )


@router.get("/rooms")
def list_rooms():
    """
    List all available game rooms (HTTP endpoint for convenience).
    
    Returns rooms that haven't started yet.
    """
    from app.settings.lifespan import room_manager
    return {"rooms": room_manager.list_rooms() if room_manager else []}


# ============================================================================
# WebSocket Message Type Definitions (for TypeScript generation)
# ============================================================================

@router.post("/websocket-messages/join-game", response_model=JoinGameMessage, tags=["WebSocket Messages"], include_in_schema=True)
async def _ws_join_game_type(msg: JoinGameMessage) -> JoinGameMessage:
    """WebSocket message type: join_game (dummy endpoint for type generation)."""
    return msg

@router.post("/websocket-messages/list-rooms", response_model=ListRoomsMessage, tags=["WebSocket Messages"], include_in_schema=True)
async def _ws_list_rooms_type(msg: ListRoomsMessage) -> ListRoomsMessage:
    """WebSocket message type: list_rooms (dummy endpoint for type generation)."""
    return msg

@router.post("/websocket-messages/action", response_model=ActionMessage, tags=["WebSocket Messages"], include_in_schema=True)
async def _ws_action_type(msg: ActionMessage) -> ActionMessage:
    """WebSocket message type: action (dummy endpoint for type generation)."""
    return msg

@router.post("/websocket-messages/get-state", response_model=GetStateMessage, tags=["WebSocket Messages"], include_in_schema=True)
async def _ws_get_state_type(msg: GetStateMessage) -> GetStateMessage:
    """WebSocket message type: get_state (dummy endpoint for type generation)."""
    return msg

@router.post("/websocket-messages/get-valid-actions", response_model=GetValidActionsMessage, tags=["WebSocket Messages"], include_in_schema=True)
async def _ws_get_valid_actions_type(msg: GetValidActionsMessage) -> GetValidActionsMessage:
    """WebSocket message type: get_valid_actions (dummy endpoint for type generation)."""
    return msg

@router.post("/websocket-messages/leave-game", response_model=LeaveGameMessage, tags=["WebSocket Messages"], include_in_schema=True)
async def _ws_leave_game_type(msg: LeaveGameMessage) -> LeaveGameMessage:
    """WebSocket message type: leave_game (dummy endpoint for type generation)."""
    return msg

@router.post("/websocket-messages/ping", response_model=PingMessage, tags=["WebSocket Messages"], include_in_schema=True)
async def _ws_ping_type(msg: PingMessage) -> PingMessage:
    """WebSocket message type: ping (dummy endpoint for type generation)."""
    return msg

# Server → Client Messages (return types)
@router.get("/websocket-messages/connected", response_model=ConnectedMessage, tags=["WebSocket Messages"], include_in_schema=True)
async def _ws_connected_type() -> ConnectedMessage:
    """WebSocket message type: connected (dummy endpoint for type generation)."""
    return ConnectedMessage()

@router.get("/websocket-messages/game-created", response_model=GameCreatedMessage, tags=["WebSocket Messages"], include_in_schema=True)
async def _ws_game_created_type() -> GameCreatedMessage:
    """WebSocket message type: game_created (dummy endpoint for type generation)."""
    return GameCreatedMessage()

@router.get("/websocket-messages/game-joined", response_model=GameJoinedMessage, tags=["WebSocket Messages"], include_in_schema=True)
async def _ws_game_joined_type() -> GameJoinedMessage:
    """WebSocket message type: game_joined (dummy endpoint for type generation)."""
    return GameJoinedMessage()

@router.get("/websocket-messages/player-joined", response_model=PlayerJoinedMessage, tags=["WebSocket Messages"], include_in_schema=True)
async def _ws_player_joined_type() -> PlayerJoinedMessage:
    """WebSocket message type: player_joined (dummy endpoint for type generation)."""
    return PlayerJoinedMessage()

@router.get("/websocket-messages/player-left", response_model=PlayerLeftMessage, tags=["WebSocket Messages"], include_in_schema=True)
async def _ws_player_left_type() -> PlayerLeftMessage:
    """WebSocket message type: player_left (dummy endpoint for type generation)."""
    return PlayerLeftMessage()

@router.get("/websocket-messages/game-started", response_model=GameStartedMessage, tags=["WebSocket Messages"], include_in_schema=True)
async def _ws_game_started_type() -> GameStartedMessage:
    """WebSocket message type: game_started (dummy endpoint for type generation)."""
    return GameStartedMessage()

@router.get("/websocket-messages/game-state", response_model=GameStateMessage, tags=["WebSocket Messages"], include_in_schema=True)
async def _ws_game_state_type() -> GameStateMessage:
    """WebSocket message type: game_state (dummy endpoint for type generation)."""
    return GameStateMessage()

@router.get("/websocket-messages/action-result", response_model=ActionResultMessage, tags=["WebSocket Messages"], include_in_schema=True)
async def _ws_action_result_type() -> ActionResultMessage:
    """WebSocket message type: action_result (dummy endpoint for type generation)."""
    return ActionResultMessage()

@router.get("/websocket-messages/valid-actions", response_model=ValidActionsMessage, tags=["WebSocket Messages"], include_in_schema=True)
async def _ws_valid_actions_type() -> ValidActionsMessage:
    """WebSocket message type: valid_actions (dummy endpoint for type generation)."""
    return ValidActionsMessage()

@router.get("/websocket-messages/rooms-list", response_model=RoomsListMessage, tags=["WebSocket Messages"], include_in_schema=True)
async def _ws_rooms_list_type() -> RoomsListMessage:
    """WebSocket message type: rooms_list (dummy endpoint for type generation)."""
    return RoomsListMessage()

@router.get("/websocket-messages/game-left", response_model=GameLeftMessage, tags=["WebSocket Messages"], include_in_schema=True)
async def _ws_game_left_type() -> GameLeftMessage:
    """WebSocket message type: game_left (dummy endpoint for type generation)."""
    return GameLeftMessage()

@router.get("/websocket-messages/error", response_model=ErrorMessage, tags=["WebSocket Messages"], include_in_schema=True)
async def _ws_error_type() -> ErrorMessage:
    """WebSocket message type: error (dummy endpoint for type generation)."""
    return ErrorMessage()

@router.get("/websocket-messages/pong", response_model=PongMessage, tags=["WebSocket Messages"], include_in_schema=True)
async def _ws_pong_type() -> PongMessage:
    """WebSocket message type: pong (dummy endpoint for type generation)."""
    return PongMessage()

