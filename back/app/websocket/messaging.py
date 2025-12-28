"""
WebSocket Messaging

Publishes messages to broadcaster channels.
This is a thin wrapper around broadcaster.publish() for convenience.

Architecture:
- This module PUBLISHES messages to channels (one-way: server -> channels)
- connection.py SUBSCRIBES to channels and forwards to WebSocket (channels -> WebSocket)
- The broadcaster library handles the pub/sub distribution (supports Redis for scaling)
"""

from pydantic import BaseModel

from broadcaster import Broadcast


class MessageBroadcaster:
    """
    Publishes messages to broadcaster channels.
    
    This does NOT manage queues or WebSocket connections.
    It simply publishes messages to channels. The ConnectionManager
    subscribes to these channels and forwards messages to WebSocket connections.
    """
    
    def __init__(self, broadcast: Broadcast):
        self.broadcast = broadcast
    
    async def send_to_player(self, player_id: str, message: dict | BaseModel) -> bool:
        """
        Publish a message to a player-specific channel.
        
        The ConnectionManager subscribes to this channel and forwards
        the message to the player's WebSocket connection.
        """
        try:
            # Convert Pydantic model to dict if needed
            if isinstance(message, BaseModel):
                message_dict = message.model_dump(mode='json')
            else:
                message_dict = message
            
            # Publish to player-specific channel
            # ConnectionManager will pick this up and forward to WebSocket
            channel = f"player:{player_id}"
            await self.broadcast.publish(channel=channel, message=message_dict)
            return True
        except Exception:
            return False
    
    async def broadcast_to_room(
        self, 
        room_id: str, 
        message: dict | BaseModel
    ) -> None:
        """
        Publish a message to a room channel.
        
        All players subscribed to this room channel will receive the message.
        ConnectionManager subscribes players to room channels when they join.
        
        Args:
            room_id: The room ID to broadcast to
            message: The message to send
        """
        try:
            # Convert Pydantic model to dict if needed
            if isinstance(message, BaseModel):
                message_dict = message.model_dump(mode='json')
            else:
                message_dict = message
            
            # Publish to room channel
            # All ConnectionManagers subscribed to this room will forward to their WebSockets
            channel = f"room:{room_id}"
            await self.broadcast.publish(channel=channel, message=message_dict)
        except Exception:
            pass

