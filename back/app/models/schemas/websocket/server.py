"""
Server → Client WebSocket Message Schemas

These schemas define messages sent from server to client.
"""

from typing import Annotated, ClassVar, Literal

from pydantic import BaseModel, Field, SkipValidation

from app.models.game.events import GameEventUnion
from app.models.game.room import GameRoom, RoomSummary
from app.models.game.state import GameState, GameStateForPlayer

# Import WebSocketMessage - defined in __init__.py
from app.models.schemas.websocket import WebSocketMessage
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

    room: Annotated[GameRoom, SkipValidation]


class GameJoinedData(BaseModel):
    """Data for game_joined message."""

    room: Annotated[GameRoom, SkipValidation]


class PlayerJoinedData(BaseModel):
    """Data for player_joined message."""

    player_id: str
    name: str
    room: Annotated[GameRoom, SkipValidation]


class PlayerLeftData(BaseModel):
    """Data for player_left message."""

    player_id: str
    room: Annotated[GameRoom, SkipValidation]


class GameStartedData(BaseModel):
    """Data for game_started message."""

    success: bool
    game_state: GameStateForPlayer
    events: list[GameEventUnion]
    valid_actions: list[ValidActionSchema] = Field(default_factory=list)


class GameStateData(BaseModel):
    """Data for game_state message."""

    state: GameState | None = None


class ActionResultData(BaseModel):
    """Data for action_result message."""

    success: bool
    error: str | None = None
    events: list[GameEventUnion]
    game_over: bool
    winner_id: str | None = None
    game_state: GameStateForPlayer | None = None
    valid_actions: list[ValidActionSchema] = Field(default_factory=list)


class ValidActionsData(BaseModel):
    """Data for valid_actions message."""

    actions: list[ValidActionSchema]


class RoomsListData(BaseModel):
    """Data for rooms_list message."""

    rooms: list[RoomSummary]


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
