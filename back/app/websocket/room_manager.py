"""
Room Manager

Handles game room lifecycle: creation, joining, leaving, and game operations.
"""

import traceback
from typing import Optional, TYPE_CHECKING
from uuid import uuid4

from app.websocket.models import GameRoom
from app.websocket.connection import ConnectionManager
from app.game.engine import get_engine
from app.websocket.serialization import serialize_events, serialize_events_for_player
from app.models.schemas.websocket.server import (
    ErrorMessage,
    ErrorData,
    GameJoinedMessage,
    GameJoinedData,
    PlayerJoinedMessage,
    PlayerJoinedData,
    PlayerLeftMessage,
    PlayerLeftData,
    GameStartedMessage,
    GameStartedData,
    ActionResultMessage,
    ActionResultData,
)

if TYPE_CHECKING:
    from app.models.game.player import PlayerState


class RoomManager:
    """
    Manages game room lifecycle.
    
    Responsibilities:
    - Creating new rooms
    - Players joining/leaving rooms
    - Room state tracking
    - Starting games
    - Processing game actions
    """
    
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
        self.rooms: dict[str, GameRoom] = {}
        self.player_rooms: dict[str, str] = {}
        self.engine = get_engine()

    async def create_room(self, player: "PlayerState") -> GameRoom:
        """Create a new room with the player as host."""
        room = GameRoom(
            room_id=str(uuid4()),
            host_id=player.player_id,
        )
        await self.connection_manager.subscribe_to_room(player.player_id, room.room_id)

        room.add_player(player)
        
        self.rooms[room.room_id] = room
        self.player_rooms[player.player_id] = room.room_id
        
        return room
    
    async def join_room(self, player: "PlayerState", room_id: str) -> Optional[GameRoom]:
        """Join an existing room."""
        if room_id not in self.rooms:
            await self._send_join_error(player.player_id)
            return None

        room = self.rooms[room_id]

        if not room.can_join:
            await self._send_join_error(player.player_id)
            return None
        
        await self.connection_manager.subscribe_to_room(player.player_id, room_id)
        room.add_player(player)
        
        await self.connection_manager.send_to_player(
            player.player_id,
            GameJoinedMessage(data=GameJoinedData(room=room.model_dump(mode='json')))
        )

        self.player_rooms[player.player_id] = room_id

        await self.connection_manager.send_to_room(
            room_id,
            PlayerJoinedMessage(
                data=PlayerJoinedData(
                    player_id=player.player_id,
                    name=player.name,
                    room=room.model_dump(mode='json'),
                )
            )
        )
        
        if room.game_ready_to_start():
            await self.start_game(room)
        
        return room
    
    async def leave_room(self, player_id: str, room_id: str) -> None:
        """Leave a game room."""
        room = self.rooms.get(room_id)
        if not room:
            return
            
        room.remove_player(player_id)
        self.player_rooms.pop(player_id, None)

        await self.connection_manager.unsubscribe_from_room(player_id, room_id)
        
        await self.connection_manager.send_to_room(
            room_id,
            PlayerLeftMessage(
                data=PlayerLeftData(
                    player_id=player_id,
                    room=room.model_dump(mode='json'),
                )
            )
        )
        
        if not room.get_player_ids():
            del self.rooms[room_id]
    
    def get_room(self, room_id: str) -> Optional[GameRoom]:
        """Get a room by ID."""
        return self.rooms.get(room_id)
    
    def get_player_room(self, player_id: str) -> Optional[str]:
        """Get the room ID for a player."""
        return self.player_rooms.get(player_id)
    
    def list_rooms(self) -> list[dict]:
        """List all rooms."""
        return [room.model_dump(mode='json') for room in self.rooms.values()]
    
    async def start_game(self, room: GameRoom) -> dict:
        """
        Start a game in a room.
        
        Creates initial game state, sets up decks, and broadcasts to players.
        """
        state = self.engine.create_game(room)
        room.state = state
        
        result = self.engine.start_game(state)
        
        if result.success and result.state:
            room.state = result.state
            room.state.room.players = result.final_players
        
        for pid in room.get_player_ids():
            player_data = GameStartedData(
                success=True,
                game_state=result.state,
                events=serialize_events_for_player(result.events, pid),
                valid_actions=result.valid_actions,
            )
            await self.connection_manager.send_to_player(
                pid,
                GameStartedMessage(data=player_data),
            )
        
        return {
            "success": True,
            "game_state": result.state.model_dump(mode='json') if result.state else None,
            "events": serialize_events(result.events),
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
        
        result = self.engine.process_action_from_dict(room.state, player_id, action_data)
        
        if result.success and result.state:
            room.state = result.state
        
        for pid in room.get_player_ids():
            player_data = ActionResultData(
                success=result.success,
                error=result.error,
                events=serialize_events_for_player(result.events, pid),
                game_over=result.game_over,
                winner_id=result.winner_id,
                game_state=result.state,
                valid_actions=result.valid_actions,
            )
            await self.connection_manager.send_to_player(
                pid,
                ActionResultMessage(data=player_data),
            )
        
        return {
            "success": result.success,
            "error": result.error,
            "events": serialize_events(result.events),
            "game_over": result.game_over,
            "winner_id": result.winner_id,
            "game_state": result.state.model_dump(mode='json') if result.state else None,
        }
    
    def get_valid_actions(self, player_id: str, room_id: str) -> list[dict]:
        """Get valid actions for a player."""
        room = self.get_room(room_id)
        if not room or not room.state:
            return []
        
        if player_id not in room.get_player_ids():
            return []
        
        return self.engine.get_valid_actions(room.state)
    
    def get_game_state(self, room_id: str) -> Optional[dict]:
        """Get current game state."""
        room = self.get_room(room_id)
        if not room or not room.state:
            return None
        return room.state.model_dump(mode='json')
    
    async def _send_join_error(self, player_id: str) -> None:
        """Send a join error to a player."""
        await self.connection_manager.send_to_player(
            player_id,
            ErrorMessage(data=ErrorData(message=f"Failed to join room:\n{traceback.format_exc()}"))
        )
