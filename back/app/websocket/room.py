"""
Game Room Management

Handles game room creation, joining, and leaving.
"""

from typing import Optional
from uuid import uuid4

from app.websocket.models import GameRoom, PlayerConnection
from app.websocket.messaging import MessageBroadcaster
from app.models.schemas.websocket.server import (
    PlayerJoinedMessage,
    PlayerJoinedData,
    PlayerLeftMessage,
    PlayerLeftData,
)


class RoomManager:
    """Manages game rooms."""
    
    def __init__(self, connection_manager, message_broadcaster: MessageBroadcaster):
        self.connection_manager = connection_manager
        self.message_broadcaster = message_broadcaster
        self.rooms: dict[str, GameRoom] = {}  # room_id -> room
        self.player_rooms: dict[str, str] = {}  # player_id -> room_id
    
    async def create_room(self, player_id: str) -> GameRoom:
        """Create a new game room."""
        connection = self.connection_manager.get_connection(player_id)
        if not connection:
            raise ValueError("Player not connected")
        
        room = GameRoom(
            room_id=str(uuid4()),
            host_id=player_id,
        )
        room.add_player(player_id, connection.name, connection)
        
        self.rooms[room.room_id] = room
        self.player_rooms[player_id] = room.room_id
        
        connection.game_id = room.room_id
        
        return room
    
    async def join_room(self, player_id: str, room_id: str) -> GameRoom:
        """Join an existing game room."""
        connection = self.connection_manager.get_connection(player_id)
        if not connection:
            raise ValueError("Player not connected")
        
        if room_id not in self.rooms:
            raise ValueError("Room not found")
        
        room = self.rooms[room_id]
        
        if room.is_full:
            raise ValueError("Room is full")
        
        if room.is_started:
            raise ValueError("Game already started")
        
        room.add_player(player_id, connection.name, connection)
        self.player_rooms[player_id] = room_id
        connection.game_id = room_id
        
        # Notify other players
        await self.message_broadcaster.broadcast_to_room(
            room_id,
            PlayerJoinedMessage(
                data=PlayerJoinedData(
                    player_id=player_id,
                    name=connection.name,
                    room=room.model_dump(mode='json'),
                )
            ),
            exclude=player_id
        )
        
        return room
    
    async def leave_room(self, player_id: str, room_id: str) -> None:
        """Leave a game room."""
        if room_id not in self.rooms:
            return
        
        room = self.rooms[room_id]
        room.remove_player(player_id)
        
        if player_id in self.player_rooms:
            del self.player_rooms[player_id]
        
        connection = self.connection_manager.get_connection(player_id)
        if connection:
            connection.game_id = None
        
        # Notify remaining players
        await self.message_broadcaster.broadcast_to_room(
            room_id,
            PlayerLeftMessage(
                data=PlayerLeftData(
                    player_id=player_id,
                    room=room.model_dump(mode='json'),
                )
            )
        )
        
        # Delete room if empty
        if not room.get_player_ids():
            del self.rooms[room_id]
    
    def get_room(self, room_id: str) -> Optional[GameRoom]:
        """Get a room by ID."""
        return self.rooms.get(room_id)
    
    def get_player_room(self, player_id: str) -> Optional[str]:
        """Get the room ID for a player."""
        return self.player_rooms.get(player_id)
    
    def list_rooms(self) -> list[dict]:
        """List all available (not started) rooms."""
        return [
            room.model_dump(mode='json')
            for room in self.rooms.values()
            if not room.is_started
        ]

