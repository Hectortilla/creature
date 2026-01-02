"""
WebSocket Message Schemas

These schemas define the structure of all WebSocket messages.
They're exposed via dummy HTTP endpoints to generate TypeScript types.
"""

# Re-export all message types for backwards compatibility
from app.models.schemas.websocket.base import *
from app.models.schemas.websocket.client import (
    CreateGameMessage,
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

__all__ = [
    # Base
    "WebSocketMessage",
    # Client data
    "CreateGameData",
    "JoinGameData",
    "ListRoomsData",
    "StartGameData",
    "ActionData",
    "GetStateData",
    "GetValidActionsData",
    "LeaveGameData",
    "PingData",
    # Server data
    "ConnectedData",
    "GameCreatedData",
    "GameJoinedData",
    "PlayerJoinedData",
    "PlayerLeftData",
    "GameStartedData",
    "GameStateData",
    "ActionResultData",
    "ValidActionsData",
    "RoomsListData",
    "GameLeftData",
    "ErrorData",
    "PongData",
    # Client messages
    "CreateGameMessage",
    "JoinGameMessage",
    "ListRoomsMessage",
    "ActionMessage",
    "GetStateMessage",
    "GetValidActionsMessage",
    "LeaveGameMessage",
    "PingMessage",
    # Server messages
    "ConnectedMessage",
    "GameCreatedMessage",
    "GameJoinedMessage",
    "PlayerJoinedMessage",
    "PlayerLeftMessage",
    "GameStartedMessage",
    "GameStateMessage",
    "ActionResultMessage",
    "ValidActionsMessage",
    "RoomsListMessage",
    "GameLeftMessage",
    "ErrorMessage",
    "PongMessage",
]

