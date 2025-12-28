"""
Server → Client WebSocket Message Schemas

These schemas define messages sent from server to client.
"""

from typing import ClassVar, Literal
from pydantic import Field

from app.models.schemas.websocket.base import (
    WebSocketMessage,
    ConnectedData,
    GameCreatedData,
    GameJoinedData,
    PlayerJoinedData,
    PlayerLeftData,
    GameStartedData,
    GameStateData,
    ActionResultData,
    ValidActionsData,
    RoomsListData,
    GameLeftData,
    ErrorData,
    PongData,
)


# ============================================================================
# Server → Client Messages
# ============================================================================

class ConnectedMessage(WebSocketMessage):
    """Connection established."""
    type: ClassVar[Literal["connected"]] = "connected"
    data: ConnectedData


class GameCreatedMessage(WebSocketMessage):
    """Game room created successfully."""
    type: ClassVar[Literal["game_created"]] = "game_created"
    data: GameCreatedData


class GameJoinedMessage(WebSocketMessage):
    """Successfully joined a game."""
    type: ClassVar[Literal["game_joined"]] = "game_joined"
    data: GameJoinedData


class PlayerJoinedMessage(WebSocketMessage):
    """Another player joined."""
    type: ClassVar[Literal["player_joined"]] = "player_joined"
    data: PlayerJoinedData


class PlayerLeftMessage(WebSocketMessage):
    """A player left."""
    type: ClassVar[Literal["player_left"]] = "player_left"
    data: PlayerLeftData


class GameStartedMessage(WebSocketMessage):
    """Game has started."""
    type: ClassVar[Literal["game_started"]] = "game_started"
    data: GameStartedData


class GameStateMessage(WebSocketMessage):
    """Full game state update."""
    type: ClassVar[Literal["game_state"]] = "game_state"
    data: GameStateData = Field(default_factory=lambda: GameStateData(state=None))


class ActionResultMessage(WebSocketMessage):
    """Result of an action."""
    type: ClassVar[Literal["action_result"]] = "action_result"
    data: ActionResultData


class ValidActionsMessage(WebSocketMessage):
    """List of valid actions."""
    type: ClassVar[Literal["valid_actions"]] = "valid_actions"
    data: ValidActionsData = Field(default_factory=lambda: ValidActionsData(actions=[]))


class RoomsListMessage(WebSocketMessage):
    """List of available rooms."""
    type: ClassVar[Literal["rooms_list"]] = "rooms_list"
    data: RoomsListData = Field(default_factory=lambda: RoomsListData(rooms=[]))


class GameLeftMessage(WebSocketMessage):
    """Left the game."""
    type: ClassVar[Literal["game_left"]] = "game_left"
    data: GameLeftData = Field(default_factory=GameLeftData)


class ErrorMessage(WebSocketMessage):
    """Error message."""
    type: ClassVar[Literal["error"]] = "error"
    data: ErrorData


class PongMessage(WebSocketMessage):
    """Response to ping."""
    type: ClassVar[Literal["pong"]] = "pong"
    data: PongData = Field(default_factory=PongData)

