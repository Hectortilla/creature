"""
WebSocket Connection Management

Handles player connections and disconnections.
"""

from fastapi import WebSocket

from app.websocket.models import PlayerConnection


class ConnectionManager:
    """Manages player WebSocket connections."""
    
    def __init__(self):
        self.connections: dict[str, PlayerConnection] = {}  # player_id -> connection
    
    async def connect(self, websocket: WebSocket, player_id: str, name: str, deck: list[dict]) -> PlayerConnection:
        """Register a new player connection."""
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
        return connection
    
    async def disconnect(self, player_id: str) -> None:
        """Disconnect a player and clean up."""
        if player_id not in self.connections:
            return
        
        connection = self.connections[player_id]
        
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

