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
        # Check players dict first (after game starts)
        if self.players:
            return len(self.players) == 2
        # Otherwise check room fields (before game starts)
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
        # Count active players - prefer players dict if available
        if self.players:
            player_count = len(self.players)
        else:
            player_count = sum(1 for p in [self.player1_id, self.player2_id] if p is not None)
        return player_count == 1
    
    @computed_field
    @property
    def players_list(self) -> list[Optional[dict]]:
        """List of players for serialization."""
        # If players dict exists (after game starts), use that
        if self.players:
            return [
                {"player_id": pid, "name": player.name}
                for pid, player in self.players.items()
            ]
        # Otherwise use room fields (before game starts)
        return [
            {"player_id": self.player1_id, "name": self.player1_name}
            if self.player1_id else None,
            {"player_id": self.player2_id, "name": self.player2_name}
            if self.player2_id else None,
        ]
    
    def get_player1_id(self) -> Optional[str]:
        """Get player1_id, preferring players dict when available."""
        if self.players:
            player_list = list(self.players.keys())
            return player_list[0] if len(player_list) > 0 else None
        return self.player1_id
    
    def get_player1_name(self) -> Optional[str]:
        """Get player1_name, preferring players dict when available."""
        if self.players:
            player_list = list(self.players.values())
            return player_list[0].name if len(player_list) > 0 else None
        return self.player1_name
    
    def get_player2_id(self) -> Optional[str]:
        """Get player2_id, preferring players dict when available."""
        if self.players:
            player_list = list(self.players.keys())
            return player_list[1] if len(player_list) > 1 else None
        return self.player2_id
    
    def get_player2_name(self) -> Optional[str]:
        """Get player2_name, preferring players dict when available."""
        if self.players:
            player_list = list(self.players.values())
            return player_list[1].name if len(player_list) > 1 else None
        return self.player2_name
    
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
    
    def save_players(self, player1_id: str, player1_name: str, player2_id: str, player2_name: str) -> None:
        """Initialize players dict for the game."""
        from app.models.game.player import PlayerState
        
        self.players = {
            player1_id: PlayerState(player_id=player1_id, name=player1_name),
            player2_id: PlayerState(player_id=player2_id, name=player2_name),
        }
    
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
        # If players dict exists (after game starts), use that
        if self.players:
            return list(self.players.keys())
        # Otherwise, get from room fields (before game starts)
        ids = []
        if self.player1_id:
            ids.append(self.player1_id)
        if self.player2_id:
            ids.append(self.player2_id)
        return ids
    
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

