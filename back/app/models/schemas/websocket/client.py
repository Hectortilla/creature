"""
Client → Server WebSocket Message Schemas

These schemas define messages sent from client to server.
"""

from typing import ClassVar, Literal
from pydantic import Field

from app.models.schemas.websocket.base import (
    WebSocketMessage,
    CreateGameData,
    JoinGameData,
    ListRoomsData,
    StartGameData,
    ActionData,
    GetStateData,
    GetValidActionsData,
    LeaveGameData,
    PingData,
)


# ============================================================================
# Client → Server Messages
# ============================================================================

class CreateGameMessage(WebSocketMessage):
    """Create a new game room."""
    type: ClassVar[Literal["create_game"]] = "create_game"
    data: CreateGameData = Field(default_factory=CreateGameData)


class JoinGameMessage(WebSocketMessage):
    """Join an existing game room."""
    type: ClassVar[Literal["join_game"]] = "join_game"
    data: JoinGameData


class ListRoomsMessage(WebSocketMessage):
    """List all available game rooms."""
    type: ClassVar[Literal["list_rooms"]] = "list_rooms"
    data: ListRoomsData = Field(default_factory=ListRoomsData)


class StartGameMessage(WebSocketMessage):
    """Start the game (host only)."""
    type: ClassVar[Literal["start_game"]] = "start_game"
    data: StartGameData = Field(default_factory=StartGameData)


class ActionMessage(WebSocketMessage):
    """Perform a game action."""
    type: ClassVar[Literal["action"]] = "action"
    data: ActionData


class GetStateMessage(WebSocketMessage):
    """Request current game state."""
    type: ClassVar[Literal["get_state"]] = "get_state"
    data: GetStateData = Field(default_factory=GetStateData)


class GetValidActionsMessage(WebSocketMessage):
    """Request valid actions for player."""
    type: ClassVar[Literal["get_valid_actions"]] = "get_valid_actions"
    data: GetValidActionsData = Field(default_factory=GetValidActionsData)


class LeaveGameMessage(WebSocketMessage):
    """Leave the current game."""
    type: ClassVar[Literal["leave_game"]] = "leave_game"
    data: LeaveGameData = Field(default_factory=LeaveGameData)


class PingMessage(WebSocketMessage):
    """Keep-alive ping."""
    type: ClassVar[Literal["ping"]] = "ping"
    data: PingData = Field(default_factory=PingData)

