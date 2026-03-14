"""
Server → Client WebSocket Message Schemas

These schemas define messages sent from server to client.
"""

from typing import Any, ClassVar, Literal, Optional
from pydantic import BaseModel, Field

# Import WebSocketMessage - defined in __init__.py
from app.models.schemas.websocket import WebSocketMessage
from app.models.game.state import GameState
from app.models.game.events import GameEventUnion
from app.models.schemas.websocket.game_schemas import ValidActionSchema


# ============================================================================
# Server → Client Data Models
# ============================================================================

class ConnectedData(BaseModel):
    """Data for connected message."""
    player_id: str
    name: str
    message: str


class GameCreatedData(BaseModel):
    """Data for game_created message."""
    room: dict[str, Any]


class GameJoinedData(BaseModel):
    """Data for game_joined message."""
    room: dict[str, Any]


class PlayerJoinedData(BaseModel):
    """Data for player_joined message."""
    player_id: str
    name: str
    room: dict[str, Any]


class PlayerLeftData(BaseModel):
    """Data for player_left message."""
    player_id: str
    room: dict[str, Any]


class GameStartedData(BaseModel):
    """Data for game_started message."""
    success: bool
    game_state: dict[str, Any]
    events: list[GameEventUnion]
    valid_actions: list[ValidActionSchema] = Field(default_factory=list)


class GameStateData(BaseModel):
    """Data for game_state message."""
    state: Optional[GameState] = None


class ActionResultData(BaseModel):
    """Data for action_result message."""
    success: bool
    error: Optional[str] = None
    events: list[GameEventUnion]
    game_over: bool
    winner_id: Optional[str] = None
    game_state: Optional[dict[str, Any]] = None
    valid_actions: list[ValidActionSchema] = Field(default_factory=list)


class ValidActionsData(BaseModel):
    """Data for valid_actions message."""
    actions: list[ValidActionSchema]


class RoomsListData(BaseModel):
    """Data for rooms_list message."""
    rooms: list[dict[str, Any]]


class GameLeftData(BaseModel):
    """Data for game_left message."""
    pass  # Empty data


class ErrorData(BaseModel):
    """Data for error message."""
    message: str


class PongData(BaseModel):
    """Data for pong message."""
    pass  # Empty data


# ============================================================================
# Server → Client Messages
# ============================================================================


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

