"""
WebSocket Game System

Modular WebSocket-based game communication system.
Handles game creation, player connections, actions, and real-time state updates.
"""

from broadcaster import Broadcast

from app.websocket.models import PlayerConnection, GameRoom
from app.websocket.connection import ConnectionManager
from app.websocket.room import RoomManager
from app.websocket.game_logic import GameLogicManager
from app.websocket.messaging import MessageBroadcaster
from app.websocket.handler import MessageHandler
from app.websocket.serialization import serialize_deck_for_game, serialize_events
from app.websocket.endpoint import handle_websocket_connection, list_game_rooms


class GameManager:
    """
    Manages game rooms, connections, and message routing.
    
    Uses broadcaster for pub/sub to support multiple server instances.
    """
    
    def __init__(self, broadcast: Broadcast):        
        # Initialize managers with broadcaster
        self.connection_manager = ConnectionManager(broadcast)
        self.message_broadcaster = MessageBroadcaster(broadcast)
        self.room_manager = RoomManager(
            self.connection_manager,
            self.message_broadcaster
        )
        
        self.game_logic_manager = GameLogicManager(
            self.room_manager,
            self.message_broadcaster
        )
        
        self.message_handler = MessageHandler(
            self.connection_manager,
            self.room_manager,
            self.game_logic_manager,
            self.message_broadcaster
        )
    
    # Connection management (delegate to ConnectionManager)
    async def connect(self, websocket, player_id: str, name: str, deck: list[dict]) -> PlayerConnection:
        """Register a new player connection."""
        return await self.connection_manager.connect(websocket, player_id, name, deck)
    
    async def disconnect(self, player_id: str) -> None:
        """Disconnect a player and clean up."""
        # Leave any game room first
        room_id = self.room_manager.get_player_room(player_id)
        if room_id:
            await self.room_manager.leave_room(player_id, room_id)
        
        await self.connection_manager.disconnect(player_id)
    
    # Room management (delegate to RoomManager)
    async def create_room(self, player_id: str) -> GameRoom:
        """Create a new game room."""
        return await self.room_manager.create_room(player_id)
    
    async def join_room(self, player_id: str, room_id: str) -> GameRoom:
        """Join an existing game room."""
        return await self.room_manager.join_room(player_id, room_id)
    
    def get_room(self, room_id: str):
        """Get a room by ID."""
        return self.room_manager.get_room(room_id)
    
    def list_rooms(self) -> list[dict]:
        """List all available (not started) rooms."""
        return self.room_manager.list_rooms()
    
    # Game logic (delegate to GameLogicManager)
    async def start_game(self, player_id: str, room_id: str) -> dict:
        """Start a game in a room."""
        return await self.game_logic_manager.start_game(player_id, room_id)
    
    async def process_action(self, player_id: str, room_id: str, action_data: dict) -> dict:
        """Process a game action."""
        return await self.game_logic_manager.process_action(player_id, room_id, action_data)
    
    def get_valid_actions(self, player_id: str, room_id: str) -> list[dict]:
        """Get valid actions for a player."""
        return self.game_logic_manager.get_valid_actions(player_id, room_id)
    
    def get_game_state(self, room_id: str):
        """Get current game state."""
        return self.game_logic_manager.get_game_state(room_id)
    
    # Messaging (delegate to MessageBroadcaster)
    async def send_to_player(self, player_id: str, message) -> bool:
        """Send a message to a specific player."""
        return await self.message_broadcaster.send_to_player(player_id, message)
    
    # Message handling (delegate to MessageHandler)
    async def handle_message(self, player_id: str, message: dict) -> None:
        """Handle an incoming WebSocket message."""
        await self.message_handler.handle_message(player_id, message)
    
    # Backwards compatibility properties
    @property
    def connections(self) -> dict[str, PlayerConnection]:
        """Backwards compatibility: access to connections dict."""
        return self.connection_manager.connections
    
    @property
    def rooms(self) -> dict[str, GameRoom]:
        """Backwards compatibility: access to rooms dict."""
        return self.room_manager.rooms
    
    @property
    def player_rooms(self) -> dict[str, str]:
        """Backwards compatibility: access to player_rooms dict."""
        return self.room_manager.player_rooms


# WebSocket handler function
async def game_websocket_handler(
    websocket,
    player_id: str,
    name: str,
    manager: GameManager,
    deck: list[dict],
    room_id: str | None = None,
) -> None:
    """
    Main WebSocket handler for game connections.
    
    Args:
        websocket: The WebSocket connection
        player_id: Unique identifier for the player
        name: Display name for the player
        manager: The game manager instance
        deck: Serialized deck to use for the game
        room_id: Optional room ID to auto-join after connection
    """
    from fastapi import WebSocketDisconnect
    from app.models.schemas.websocket.server import ConnectedMessage, ConnectedData, GameJoinedMessage, GameJoinedData
    
    connection = await manager.connect(websocket, player_id, name, deck)
    
    # Send welcome message
    await manager.send_to_player(player_id, ConnectedMessage(
        data=ConnectedData(
            player_id=player_id,
            name=name,
            message="Connected to game server",
        )
    ))
    
    # Auto-join room if room_id is provided
    if room_id:
        try:
            room = await manager.join_room(player_id, room_id)
            # Send game joined message
            await manager.send_to_player(player_id, GameJoinedMessage(
                data=GameJoinedData(room=room.model_dump(mode='json'))
            ))
        except Exception as e:
            # If auto-join fails, send error but don't disconnect
            from app.models.schemas.websocket.server import ErrorMessage, ErrorData
            await manager.send_to_player(player_id, ErrorMessage(
                data=ErrorData(message=f"Failed to join room: {str(e)}")
            ))
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            await manager.handle_message(player_id, data)
    
    except WebSocketDisconnect:
        await manager.disconnect(player_id)
    except Exception:
        await manager.disconnect(player_id)


__all__ = [
    "GameManager",
    "PlayerConnection",
    "GameRoom",
    "ConnectionManager",
    "RoomManager",
    "GameLogicManager",
    "MessageBroadcaster",
    "MessageHandler",
    "serialize_deck_for_game",
    "serialize_events",
    "game_websocket_handler",
    "handle_websocket_connection",
    "list_game_rooms",
]

