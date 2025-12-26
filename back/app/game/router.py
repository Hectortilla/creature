"""
Game Models

Pydantic models for game data serialization.
These can be used for API documentation and type hints.

Note: The game now uses WebSocket communication exclusively.
See websocket.py for the WebSocket handler and game_websocket_handler.
"""

from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


# ============================================================================
# Request Models (for WebSocket message data)
# ============================================================================

class PlayerInfo(BaseModel):
    """Player information for game creation."""
    player_id: str
    name: str


class CardData(BaseModel):
    """Card data for deck building."""
    id: int
    name: str
    health: int = 10
    physical_defence: int = 0
    magic_defence: int = 0
    element_ids: list[int] = Field(default_factory=list)
    element_contribution: list[dict[str, int]] = Field(default_factory=list)
    attacks: list[dict[str, Any]] = Field(default_factory=list)
    skill_ids: list[int] = Field(default_factory=list)
    association_ids: list[int] = Field(default_factory=list)
    is_evolution: bool = False
    evolves_from_id: Optional[int] = None


# ============================================================================
# Response Models (for WebSocket message data)
# ============================================================================

class CardStateResponse(BaseModel):
    """Serialized card state."""
    instance_id: str
    card_id: int
    name: str
    owner_id: str
    current_health: int
    max_health: int
    physical_defense: int
    magical_defense: int
    element_ids: list[int]
    zone: str
    turns_in_zone: int
    can_attack: bool
    can_promote: bool
    has_attacked_this_turn: bool


class ZoneStateResponse(BaseModel):
    """Serialized zone state."""
    zone: str
    card_ids: list[str]
    max_capacity: Optional[int]
    is_full: bool


class PlayerStateResponse(BaseModel):
    """Serialized player state."""
    player_id: str
    name: str
    turn_count: int
    elements: dict[int, int]
    zones: dict[str, ZoneStateResponse]


class GameStateResponse(BaseModel):
    """Serialized game state."""
    game_id: str
    status: str
    turn_number: int
    current_phase: str
    active_player_id: Optional[str]
    winner_id: Optional[str]
    pending_action: Optional[str] = None
    players: dict[str, PlayerStateResponse]
    cards: dict[str, CardStateResponse]


class EventResponse(BaseModel):
    """Serialized game event."""
    event_type: str
    timestamp: str
    data: dict[str, Any]


class ActionResponse(BaseModel):
    """Response to a game action."""
    success: bool
    error: Optional[str] = None
    events: list[EventResponse] = Field(default_factory=list)
    game_over: bool = False
    winner_id: Optional[str] = None
    game_state: Optional[GameStateResponse] = None


class RoomResponse(BaseModel):
    """Serialized game room."""
    room_id: str
    host_id: str
    is_full: bool
    is_started: bool
    players: list[Optional[PlayerInfo]]
    created_at: str


class ValidActionsResponse(BaseModel):
    """List of valid actions for a player."""
    actions: list[dict[str, Any]]
