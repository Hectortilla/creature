"""
Client → Server WebSocket Message Schemas

These schemas define messages sent from client to server.
"""

from typing import Any, ClassVar, Literal, Optional
from pydantic import BaseModel, Field

# Import WebSocketMessage - defined in __init__.py
from app.models.schemas.websocket import WebSocketMessage


# ============================================================================
# Client → Server Data Models
# ============================================================================

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
    instance_id: Optional[str] = Field(
        default=None,
        description="Card instance ID (used by: promote, force_defend)",
        examples=["card_instance_123"]
    )
    instance_ids: list[str] = Field(
        default_factory=list,
        description="List of card instance IDs (used by: play_card)",
        examples=[["card_instance_123", "card_instance_456"]]
    )
    count: int = Field(
        default=1,
        description="Number of cards to draw (used by: draw)",
        examples=[1, 2, 3]
    )
    target_card_id: Optional[str] = Field(
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


# ============================================================================
# Client → Server Messages
# ============================================================================


# ============================================================================
# Client → Server Messages
# ============================================================================

class JoinGameMessage(WebSocketMessage):
    """Join an existing game room."""
    type: ClassVar[Literal["join_game"]] = "join_game"
    data: JoinGameData


class ListRoomsMessage(WebSocketMessage):
    """List all available game rooms."""
    type: ClassVar[Literal["list_rooms"]] = "list_rooms"
    data: ListRoomsData = Field(default_factory=ListRoomsData)



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

