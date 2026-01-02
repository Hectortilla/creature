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

from app.models.game import GameState, GameBaseModel, GameStatus, PlayerState


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
    players: dict[str, PlayerState] = Field(default_factory=dict)  # Player ID -> PlayerState
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
        return len(self.players) == 2
    
    @computed_field
    @property
    def is_started(self) -> bool:
        return self.state is not None and self.state.status != GameStatus.WAITING
    
    @computed_field
    @property
    def can_join(self) -> bool:
        return len(self.players) < 2 and not self.is_started
    
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
    
    def add_player(self, player_id: str, name: str, connection: PlayerConnection) -> int:
        """Add a player to the room. Returns slot number (1 or 2)."""
        if connection.deck is None:
            raise ValueError("Player connection does not have a deck")
        
        if len(self.players) == 2:
            raise ValueError("Room is full")

        self.players[player_id] = PlayerState(player_id=player_id, name=name)
    
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
        if not self.state:
            return False
        if self.state.status != GameStatus.STARTING:
            return False
        if len(self.players) != 2:
            return False
        # Check deck sizes using config
        from app.models.game.enums import Zone
        deck_size = self.state.config.deck_size
        player_list = list(self.players.values())
        if len(player_list) < 2:
            return False
        if len(player_list[0].zones[Zone.DECK.name].card_ids) != deck_size:
            return False
        if len(player_list[1].zones[Zone.DECK.name].card_ids) != deck_size:
            return False
        return True

