"""
WebSocket Message Schemas

These schemas define the structure of all WebSocket messages.
They're exposed via dummy HTTP endpoints to generate TypeScript types.
"""

from typing import Any, ClassVar, Literal, Optional
from pydantic import BaseModel, Field

# ============================================================================
# Data Models for Message Payloads
# ============================================================================

class CreateGameData(BaseModel):
    """Data for create_game message."""
    pass  # Empty data


class JoinGameData(BaseModel):
    """Data for join_game message."""
    room_id: str


class ListRoomsData(BaseModel):
    """Data for list_rooms message."""
    pass  # Empty data


class StartGameData(BaseModel):
    """Data for start_game message."""
    pass  # Empty data


class ActionData(BaseModel):
    """Data for action message."""
    action_type: str
    card_id: Optional[str] = None
    card_ids: list[str] = Field(default_factory=list)
    count: int = 1
    target_id: Optional[str] = None
    attacker_id: Optional[str] = None
    attack_id: Optional[str] = None
    supporting_card_id: Optional[str] = None
    attacking_card_id: Optional[str] = None
    swaps: list[dict[str, Any]] = Field(default_factory=list)
    association_card_id: Optional[str] = None
    evolution_card_id: Optional[str] = None


class GetStateData(BaseModel):
    """Data for get_state message."""
    pass  # Empty data


class GetValidActionsData(BaseModel):
    """Data for get_valid_actions message."""
    pass  # Empty data


class LeaveGameData(BaseModel):
    """Data for leave_game message."""
    pass  # Empty data


class PingData(BaseModel):
    """Data for ping message."""
    pass  # Empty data


class ConnectedData(BaseModel):
    """Data for connected message."""
    player_id: str
    name: str
    message: str


class GameCreatedData(BaseModel):
    """Data for game_created message."""
    room: dict[str, Any]  # GameRoom serialized


class GameJoinedData(BaseModel):
    """Data for game_joined message."""
    room: dict[str, Any]  # GameRoom serialized


class PlayerJoinedData(BaseModel):
    """Data for player_joined message."""
    player_id: str
    name: str
    room: dict[str, Any]  # GameRoom serialized


class PlayerLeftData(BaseModel):
    """Data for player_left message."""
    player_id: str
    room: dict[str, Any]  # GameRoom serialized


class GameStartedData(BaseModel):
    """Data for game_started message."""
    success: bool
    game_state: dict[str, Any]  # GameState serialized
    events: list[dict[str, Any]]  # List of serialized events


class GameStateData(BaseModel):
    """Data for game_state message."""
    state: Optional[dict[str, Any]] = None  # GameState serialized or None


class ActionResultData(BaseModel):
    """Data for action_result message."""
    success: bool
    error: Optional[str] = None
    events: list[dict[str, Any]]  # List of serialized events
    game_over: bool
    winner_id: Optional[str] = None
    game_state: Optional[dict[str, Any]] = None  # GameState serialized or None


class ValidActionsData(BaseModel):
    """Data for valid_actions message."""
    actions: list[dict[str, Any]]  # List of valid action dictionaries


class RoomsListData(BaseModel):
    """Data for rooms_list message."""
    rooms: list[dict[str, Any]]  # List of GameRoom serialized


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
# Base Message Class
# ============================================================================

class WebSocketMessage(BaseModel):
    """Base class for WebSocket messages that ensures type is included in serialization."""
    
    def model_dump(self, **kwargs) -> dict[str, Any]:
        """Override to include the ClassVar type in serialization."""
        result = super().model_dump(**kwargs)
        # Include the type from the class variable
        result['type'] = self.__class__.type
        return result

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

