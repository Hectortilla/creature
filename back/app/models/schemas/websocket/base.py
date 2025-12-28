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
    """Data for action message.
    
    This model represents all possible fields for game actions.
    Different action types use different subsets of these fields.
    """
    action_type: str = Field(
        description="The type of action to perform",
        examples=["draw", "play_card", "promote", "swap", "associate", "evolve", "attack", "pass", "concede"]
    )
    card_id: Optional[str] = Field(
        default=None,
        description="Card instance ID (used by: play_card, promote, force_defend)",
        examples=["card_instance_123"]
    )
    card_ids: list[str] = Field(
        default_factory=list,
        description="List of card instance IDs (used by: multi_play_card)",
        examples=[["card_instance_123", "card_instance_456"]]
    )
    count: int = Field(
        default=1,
        description="Number of cards to draw (used by: draw)",
        examples=[1, 2, 3]
    )
    target_id: Optional[str] = Field(
        default=None,
        description="Target card instance ID (used by: associate, evolve, attack)",
        examples=["card_instance_789"]
    )
    attacker_id: Optional[str] = Field(
        default=None,
        description="Attacker card instance ID (used by: attack)",
        examples=["card_instance_123"]
    )
    attack_id: Optional[str] = Field(
        default=None,
        description="Attack ID to use (used by: attack)",
        examples=["1", "2"]
    )
    supporting_card_id: Optional[str] = Field(
        default=None,
        description="Supporting card instance ID (used by: swap)",
        examples=["card_instance_123"]
    )
    attacking_card_id: Optional[str] = Field(
        default=None,
        description="Attacking card instance ID (used by: swap)",
        examples=["card_instance_456"]
    )
    swaps: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of swap pairs (used by: multi_swap). Each swap is {supporting_card_id: str, attacking_card_id: str}",
        examples=[[{"supporting_card_id": "card_1", "attacking_card_id": "card_2"}]]
    )
    association_card_id: Optional[str] = Field(
        default=None,
        description="Association card instance ID (used by: associate)",
        examples=["card_instance_123"]
    )
    evolution_card_id: Optional[str] = Field(
        default=None,
        description="Evolution card instance ID (used by: evolve)",
        examples=["card_instance_123"]
    )


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

