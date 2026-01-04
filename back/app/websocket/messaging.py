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
        if isinstance(message, BaseModel):
            message_dict = message.model_dump(mode='json')
        else:
            message_dict = message
        channel = f"player:{player_id}"
        await self.broadcast.publish(channel=channel, message=message_dict)
    
    async def broadcast_to_room(
        self, 
        room_id: str, 
        message: dict | BaseModel
    ) -> None:
        if isinstance(message, BaseModel):
            message_dict = message.model_dump(mode='json')
        else:
            message_dict = message
        channel = f"room:{room_id}"
        await self.broadcast.publish(channel=channel, message=message_dict)
