"""
WebSocket Message Base Classes and Data Models

Base classes and data payload models for WebSocket messages.
"""

from typing import Any, Optional
from pydantic import BaseModel, Field


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
# Data Models for Message Payloads
# ============================================================================

# Client → Server Data Models
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


# Server → Client Data Models
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
    valid_actions: list[dict[str, Any]] = Field(default_factory=list)  # Valid actions for the active player


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
    valid_actions: list[dict[str, Any]] = Field(default_factory=list)  # Valid actions for the acting player


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

