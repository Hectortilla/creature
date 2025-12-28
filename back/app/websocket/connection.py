"""
WebSocket Connection Management

Manages WebSocket connections and subscribes to broadcaster channels.

Architecture:
- When a player connects, we subscribe to their player channel (player:{id})
- When they join a room, we also subscribe to the room channel (room:{id})
- Messages published to these channels (by MessageBroadcaster) are forwarded to the WebSocket
- The queue is used to merge messages from multiple channel subscriptions into one stream
"""

import asyncio
from typing import Optional, Set
from fastapi import WebSocket

from broadcaster import Broadcast
from app.websocket.models import PlayerConnection


class ConnectionManager:
    """Manages player WebSocket connections with broadcaster subscriptions."""
    
    def __init__(self, broadcast: Broadcast):
        self.broadcast = broadcast
        self.connections: dict[str, PlayerConnection] = {}  # player_id -> connection
        self._subscription_tasks: dict[str, asyncio.Task] = {}  # player_id -> subscription task
        self._active_channels: dict[str, Set[str]] = {}  # player_id -> set of channel names
    
    async def connect(self, websocket: WebSocket, player_id: str, name: str, deck: list[dict]) -> PlayerConnection:
        """Register a new player connection and subscribe to channels."""
        await websocket.accept()
        
        # Disconnect existing connection if any
        if player_id in self.connections:
            await self.disconnect(player_id)
        
        connection = PlayerConnection(
            player_id=player_id,
            name=name,
            websocket=websocket,
            deck=deck,
        )
        self.connections[player_id] = connection
        
        # Subscribe to player-specific channel
        player_channel = f"player:{player_id}"
        self._active_channels[player_id] = {player_channel}
        
        # Start background task to forward messages from broadcaster to WebSocket
        # Note: The subscription is established asynchronously, so the initial connection
        # message should be sent directly to WebSocket (see game_websocket_handler)
        task = asyncio.create_task(self._forward_messages(player_id))
        self._subscription_tasks[player_id] = task
        
        return connection
    
    async def _forward_messages(self, player_id: str) -> None:
        """
        Subscribe to broadcaster channels and forward messages to WebSocket.
        
        This method:
        1. Subscribes to all active channels for this player (player channel + room channels)
        2. Uses a queue to merge messages from multiple channel subscriptions
        3. Forwards messages from the queue to the WebSocket connection
        
        The queue is necessary because a player can be subscribed to multiple channels
        (their own player channel + room channels), and we need to merge these into
        a single stream to send to the WebSocket.
        """
        connection = self.connections.get(player_id)
        if not connection:
            return
        
        # Queue to merge messages from multiple channel subscriptions
        message_queue: asyncio.Queue = asyncio.Queue()
        channels = self._active_channels.get(player_id, set()).copy()
        if not channels:
            return
        
        async def subscribe_to_channel(channel: str):
            """
            Subscribe to a broadcaster channel and forward messages to the queue.
            
            This runs concurrently for each channel (player channel, room channels, etc.)
            All messages from all channels end up in the same queue, which is then
            forwarded to the WebSocket in order.
            """
            try:
                async with self.broadcast.subscribe(channel=channel) as subscriber:
                    async for event in subscriber:
                        if player_id not in self.connections:
                            break
                        # Put message in queue to be forwarded to WebSocket
                        try:
                            message_queue.put_nowait(event.message)
                        except asyncio.QueueFull:
                            pass  # Skip if queue is full (shouldn't happen with unbounded queue)
            except asyncio.CancelledError:
                raise
            except Exception:
                pass
        
        # Start subscription tasks for all channels (player + room channels)
        subscription_tasks = [
            asyncio.create_task(subscribe_to_channel(ch)) 
            for ch in channels
        ]
        
        try:
            # Forward messages from queue to WebSocket
            while True:
                try:
                    # Wait for message with timeout to periodically check connection status
                    message = await asyncio.wait_for(message_queue.get(), timeout=1.0)
                    
                    if player_id not in self.connections:
                        break
                    conn = self.connections.get(player_id)
                    if not conn or conn.websocket.client_state.name != "CONNECTED":
                        break
                    
                    # Forward message from broadcaster channel to WebSocket
                    try:
                        await conn.websocket.send_json(message)
                    except Exception:
                        # Connection closed
                        break
                except asyncio.TimeoutError:
                    # Periodic check: ensure connection still exists
                    if player_id not in self.connections:
                        break
                    continue
        except asyncio.CancelledError:
            raise
        finally:
            # Clean up: cancel all subscription tasks
            for task in subscription_tasks:
                task.cancel()
            # Wait for them to finish
            await asyncio.gather(*subscription_tasks, return_exceptions=True)
    
    async def subscribe_to_room(self, player_id: str, room_id: str) -> None:
        """Subscribe a player to a room channel."""
        if player_id not in self.connections:
            return
        
        room_channel = f"room:{room_id}"
        
        # Add room channel to active channels
        if player_id not in self._active_channels:
            self._active_channels[player_id] = set()
        self._active_channels[player_id].add(room_channel)
        
        # Restart the forwarding task to include the new channel
        if player_id in self._subscription_tasks:
            self._subscription_tasks[player_id].cancel()
            try:
                await self._subscription_tasks[player_id]
            except asyncio.CancelledError:
                pass
        
        # Start new task with updated channels
        task = asyncio.create_task(self._forward_messages(player_id))
        self._subscription_tasks[player_id] = task
    
    async def unsubscribe_from_room(self, player_id: str, room_id: str) -> None:
        """Unsubscribe a player from a room channel."""
        if player_id not in self.connections:
            return
        
        room_channel = f"room:{room_id}"
        
        # Remove room channel from active channels
        if player_id in self._active_channels:
            self._active_channels[player_id].discard(room_channel)
        
        # Restart the forwarding task with updated channels
        if player_id in self._subscription_tasks:
            self._subscription_tasks[player_id].cancel()
            try:
                await self._subscription_tasks[player_id]
            except asyncio.CancelledError:
                pass
        
        # Start new task with updated channels
        task = asyncio.create_task(self._forward_messages(player_id))
        self._subscription_tasks[player_id] = task
    
    async def disconnect(self, player_id: str) -> None:
        """Disconnect a player and clean up."""
        if player_id not in self.connections:
            return
        
        connection = self.connections[player_id]
        
        # Cancel subscription task
        if player_id in self._subscription_tasks:
            self._subscription_tasks[player_id].cancel()
            try:
                await self._subscription_tasks[player_id]
            except asyncio.CancelledError:
                pass
            del self._subscription_tasks[player_id]
        
        # Clean up channels
        if player_id in self._active_channels:
            del self._active_channels[player_id]
        
        # Remove connection
        del self.connections[player_id]
        
        try:
            await connection.websocket.close()
        except Exception:
            pass
    
    def get_connection(self, player_id: str) -> PlayerConnection | None:
        """Get a player connection by ID."""
        return self.connections.get(player_id)
    
    def has_connection(self, player_id: str) -> bool:
        """Check if a player is connected."""
        return player_id in self.connections

