"""
Game Room Management

Handles game room creation, joining, leaving, and game logic operations.
"""

from typing import Optional, TYPE_CHECKING
from uuid import uuid4

from app.websocket.models import GameRoom, PlayerConnection
from app.websocket.messaging import MessageBroadcaster
from app.game.engine import get_engine
from app.game.actions import create_action
from app.websocket.serialization import serialize_events

if TYPE_CHECKING:
    from app.models.game.player import PlayerState
from app.models.schemas.websocket.server import (
    PlayerJoinedMessage,
    PlayerJoinedData,
    PlayerLeftMessage,
    PlayerLeftData,
    GameStartedMessage,
    GameStartedData,
    ActionResultMessage,
    ActionResultData,
)


class RoomManager:
    """Manages game rooms and game logic operations."""
    
    def __init__(self, connection_manager, message_broadcaster: MessageBroadcaster):
        self.connection_manager = connection_manager
        self.message_broadcaster = message_broadcaster
        self.rooms: dict[str, GameRoom] = {}  # room_id -> room
        self.player_rooms: dict[str, str] = {}  # player_id -> room_id
        self._connected_players: dict[str, "PlayerState"] = {}  # player_id -> PlayerState
        self.engine = get_engine()
    
    def register_player(self, player: "PlayerState") -> None:
        """Register a connected player."""
        self._connected_players[player.player_id] = player
    
    def get_player(self, player_id: str) -> "PlayerState | None":
        """Get a connected player by ID."""
        # First try to get from connected players
        if player_id in self._connected_players:
            return self._connected_players[player_id]
        # Otherwise try to get from a room
        room_id = self.get_player_room(player_id)
        if room_id:
            room = self.get_room(room_id)
            if room and player_id in room.players:
                return room.players[player_id]
        return None
    
    async def create_room(self, player_id: str) -> GameRoom:
        """Create a new game room."""
        player = self.get_player(player_id)
        if not player:
            raise ValueError("Player not found")
        
        connection = self.connection_manager.get_connection(player_id)
        if not connection:
            raise ValueError("Player not connected")
        
        room = GameRoom(
            room_id=str(uuid4()),
            host_id=player_id,
        )
        room.add_player(player)
        
        self.rooms[room.room_id] = room
        self.player_rooms[player_id] = room.room_id
        
        connection.game_id = room.room_id
        
        # Subscribe to room channel
        await self.connection_manager.subscribe_to_room(player_id, room.room_id)
        
        return room
    
    async def join_room(self, player_id: str, room_id: str) -> GameRoom:
        """Join an existing game room."""
        player = self.get_player(player_id)
        if not player:
            raise ValueError("Player not found")
        
        connection = self.connection_manager.get_connection(player_id)
        
        if room_id not in self.rooms:
            raise ValueError("Room not found")
        
        room = self.rooms[room_id]
        
        if room.is_full:
            raise ValueError("Room is full")
        
        if room.is_started:
            raise ValueError("Game already started")
        
        # Validate that room can be joined (has exactly 1 player)
        if not room.can_join:
            raise ValueError("Room cannot be joined. Room must have exactly 1 player and game must not have started.")
        
        room.add_player(player)
        self.player_rooms[player_id] = room_id
        connection.game_id = room_id
        
        # Subscribe to room channel
        await self.connection_manager.subscribe_to_room(player_id, room_id)
        
        # Notify other players (exclude the joining player)
        message = PlayerJoinedMessage(
            data=PlayerJoinedData(
                player_id=player_id,
                name=player.name,
                room=room.model_dump(mode='json'),
            )
        )
        for other_player_id in room.get_player_ids():
            if other_player_id != player_id:
                await self.message_broadcaster.send_to_player(other_player_id, message)
        
        if room.game_ready_to_start():
            await self._start_game(room)
        
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
            # Unsubscribe from room channel
            await self.connection_manager.unsubscribe_from_room(player_id, room_id)
        
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
        return [
            room.model_dump(mode='json')
            for room in self.rooms.values()
        ]
    
    # Game logic methods (merged from GameLogicManager)
    
    async def _start_game(self, room: GameRoom) -> dict:
        """Start a game in a room."""
        # Create the game
        state = self.engine.create_game(room)
        room.state = state  # Set initial state
        
        # Start the game
        result = self.engine.start_game(state)
        
        # Update room with the final state after starting
        if result.success and result.state:
            room.state = result.state
            room.state.room.players = result.final_players
        
        # Broadcast to all players in room
        response_data = GameStartedData(
            success=True,
            game_state=result.state.model_dump(mode='json'),
            events=serialize_events(result.events),
            valid_actions=result.valid_actions,
        )
        await self.message_broadcaster.broadcast_to_room(
            room.room_id,
            GameStartedMessage(data=response_data)
        )
        
        return {
            "success": response_data.success,
            "game_state": response_data.game_state,
            "events": response_data.events,
        }
    
    async def process_action(self, player_id: str, room_id: str, action_data: dict) -> dict:
        """Process a game action."""
        room = self.get_room(room_id)
        if not room:
            raise ValueError("Room not found")
        
        if not room.state:
            raise ValueError("Game not started")
        
        if player_id not in room.get_player_ids():
            raise ValueError("Player not in this game")
        
        # Build action
        action_type = action_data.get("action_type")
        if not action_type:
            raise ValueError("Missing action_type")
        
        # Prepare action params: remove action_type
        action_params = {k: v for k, v in action_data.items() if k != "action_type"}
        
        action = create_action(action_type, player_id=player_id, **action_params)
        
        # Process action
        result = self.engine.process_action(room.state, action)
        
        if result.success and result.state:
            room.state = result.state
            # Players are already updated in the room via state.room.players
        
        # Broadcast result to all players
        response_data = ActionResultData(
            success=result.success,
            error=result.error,
            events=serialize_events(result.events),
            game_over=result.game_over,
            winner_id=result.winner_id,
            game_state=result.state.model_dump(mode='json') if result.state else None,
            valid_actions=result.valid_actions,
        )
        await self.message_broadcaster.broadcast_to_room(
            room_id,
            ActionResultMessage(data=response_data)
        )
        
        return {
            "success": response_data.success,
            "error": response_data.error,
            "events": response_data.events,
            "game_over": response_data.game_over,
            "winner_id": response_data.winner_id,
            "game_state": response_data.game_state,
        }
    
    def get_valid_actions(self, player_id: str, room_id: str) -> list[dict]:
        """Get valid actions for a player."""
        room = self.get_room(room_id)
        if not room or not room.state:
            return []
        
        if player_id not in room.get_player_ids():
            return []
        
        return self.engine.get_valid_actions(room.state, player_id)
    
    def get_game_state(self, room_id: str) -> Optional[dict]:
        """Get current game state."""
        room = self.get_room(room_id)
        if not room or not room.state:
            return None
        return room.state.model_dump(mode='json')