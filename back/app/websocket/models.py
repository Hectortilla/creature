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

from app.models.game import GameState, GameBaseModel, GameStatus


@dataclass
class PlayerConnection:
    """Represents a connected player (kept as dataclass - not serialized)."""
    player_id: str
    name: str
    websocket: WebSocket
    game_id: Optional[str] = None
    deck: Optional[list[dict]] = None  # Serialized deck stored in memory


class GameRoom(GameBaseModel):
    """
    Represents a game room/lobby.
    
    Uses Pydantic for automatic serialization via model_dump().
    """
    room_id: str
    host_id: str
    state: Optional[GameState] = None
    player1_id: Optional[str] = None
    player1_name: Optional[str] = None
    player1_deck: Optional[list[dict]] = Field(default=None, exclude=True)
    player2_id: Optional[str] = None
    player2_name: Optional[str] = None
    player2_deck: Optional[list[dict]] = Field(default=None, exclude=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    @field_serializer('created_at')
    def serialize_created_at(self, value: datetime) -> str:
        return value.isoformat()
    
    @field_serializer('state')
    def serialize_state(self, value: Optional[GameState]) -> None:
        # Don't include full state in room serialization
        return None
    
    @computed_field
    @property
    def is_full(self) -> bool:
        return self.player1_id is not None and self.player2_id is not None
    
    @computed_field
    @property
    def is_started(self) -> bool:
        return self.state is not None and self.state.status != GameStatus.WAITING
    
    @computed_field
    @property
    def can_join(self) -> bool:
        """
        Check if a room can be joined.
        
        A room can be joined if:
        - Game has never started (state is None or status is WAITING)
        - Room has exactly 1 player (not full, but has at least one player)
        """
        if self.is_started:
            return False
        # Count active players
        player_count = sum(1 for p in [self.player1_id, self.player2_id] if p is not None)
        return player_count == 1
    
    @computed_field
    @property
    def players(self) -> list[Optional[dict]]:
        """List of players for serialization."""
        return [
            {"player_id": self.player1_id, "name": self.player1_name}
            if self.player1_id else None,
            {"player_id": self.player2_id, "name": self.player2_name}
            if self.player2_id else None,
        ]
    
    def add_player(self, player_id: str, name: str, connection: PlayerConnection) -> int:
        """Add a player to the room. Returns slot number (1 or 2)."""
        if connection.deck is None:
            raise ValueError("Player connection does not have a deck")
        
        if self.player1_id is None:
            self.player1_id = player_id
            self.player1_name = name
            self.player1_deck = connection.deck
            return 1
        elif self.player2_id is None:
            self.player2_id = player_id
            self.player2_name = name
            self.player2_deck = connection.deck
            return 2
        raise ValueError("Room is full")
    
    def remove_player(self, player_id: str) -> bool:
        """Remove a player from the room."""
        if self.player1_id == player_id:
            self.player1_id = None
            self.player1_name = None
            self.player1_deck = None
            return True
        elif self.player2_id == player_id:
            self.player2_id = None
            self.player2_name = None
            self.player2_deck = None
            return True
        return False
    
    def get_player_ids(self) -> list[str]:
        """Get list of player IDs in the room."""
        ids = []
        if self.player1_id:
            ids.append(self.player1_id)
        if self.player2_id:
            ids.append(self.player2_id)
        return ids

