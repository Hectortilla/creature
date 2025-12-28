"""
WebSocket Messaging

Handles sending messages to players and broadcasting to rooms.
"""

from typing import Optional, TYPE_CHECKING
from pydantic import BaseModel

from app.websocket.connection import ConnectionManager

if TYPE_CHECKING:
    from app.websocket.room import RoomManager


class MessageBroadcaster:
    """Handles message broadcasting to players and rooms."""
    
    def __init__(self, connection_manager: ConnectionManager, room_manager: Optional["RoomManager"] = None):
        self.connection_manager = connection_manager
        self.room_manager = room_manager
    
    async def send_to_player(self, player_id: str, message: dict | BaseModel) -> bool:
        """Send a message to a specific player."""
        connection = self.connection_manager.get_connection(player_id)
        if not connection:
            return False
        
        try:
            # Convert Pydantic model to dict if needed
            if isinstance(message, BaseModel):
                message_dict = message.model_dump(mode='json')
            else:
                message_dict = message
            await connection.websocket.send_json(message_dict)
            return True
        except Exception:
            return False
    
    async def broadcast_to_room(
        self, 
        room_id: str, 
        message: dict | BaseModel, 
        exclude: Optional[str] = None
    ) -> None:
        """Broadcast a message to all players in a room."""
        room = self.room_manager.get_room(room_id)
        if not room:
            return
        
        for player_id in room.get_player_ids():
            if player_id != exclude:
                await self.send_to_player(player_id, message)

