"""
WebSocket Models

Data models for WebSocket connections and game rooms.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import uuid4

from fastapi import WebSocket
from pydantic import Field, field_serializer, computed_field

from app.models.game.state import GameState
from app.models.game.base import GameBaseModel
from app.models.game.enums import GameStatus
from app.models.game.player import PlayerState


class GameRoom(GameBaseModel):
    """
    Represents a game room/lobby.
    
    Uses Pydantic for automatic serialization via model_dump().
    """
    room_id: str
    host_id: str
    state: Optional[GameState] = Field(default=None, exclude=True)
    players: dict[str, PlayerState] = Field(default_factory=dict)  # Player ID -> PlayerState
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @field_serializer('created_at')
    def serialize_created_at(self, value: datetime) -> str:
        return value.isoformat()

    @computed_field
    @property
    def is_full(self) -> bool:
        return len(self.players) == 2
    
    @computed_field
    @property
    def is_started(self) -> bool:
        return self.state is not None and self.state.status != GameStatus.WAITING
    
    @computed_field
    @property
    def can_join(self) -> bool:
        return not self.is_full and not self.is_started
    
    def get_player(self, player_id: str) -> PlayerState:
        """Get a player's state."""
        if player_id not in self.players:
            raise ValueError(f"Player {player_id} not found in room")
        return self.players[player_id]
    
    def get_active_player(self) -> Optional[PlayerState]:
        """Get the active player's state."""
        if not self.state or not self.state.active_player_id:
            return None
        return self.players.get(self.state.active_player_id)
    
    def get_opponent(self, player_id: str) -> PlayerState:
        """Get the opponent of a given player."""
        for pid, player in self.players.items():
            if pid != player_id:
                return player
        raise ValueError(f"No opponent found for player {player_id}")
    
    def add_player(self, player: "PlayerState") -> int:
        """Add a player to the room. Returns slot number (1 or 2)."""
        if player.deck is None:
            raise ValueError("Player deck is required")
        
        if len(self.players) == 2:
            raise ValueError("Room is full")

        self.players[player.player_id] = player

    def remove_player(self, player_id: str) -> bool:
        """Remove a player from the room."""
        if player_id not in self.players:
            raise ValueError(f"Player {player_id} not found in room")
        del self.players[player_id]
    
    def get_player_ids(self) -> list[str]:
        """Get list of player IDs in the room."""
        return list(self.players.keys())
        
    
    def game_ready_to_start(self) -> bool:
        """Check if the game is ready to start."""
        if self.state:
            return False
        if len(self.players.keys()) < 2:
            return False
        return True

GameState.model_rebuild()
