"""
Game WebSocket Handler

WebSocket-based game communication system.
Handles game creation, player connections, actions, and real-time state updates.

Message Protocol:
    All messages are JSON with a "type" field:
    
    Client → Server:
        - create_game: Create a new game room
        - join_game: Join an existing game
        - start_game: Start the game (host only)
        - action: Perform a game action
        - get_state: Request current game state
        - get_valid_actions: Request valid actions for player
        - leave_game: Leave the current game
        - ping: Keep-alive
    
    Server → Client:
        - game_created: Game room created successfully
        - game_joined: Successfully joined a game
        - player_joined: Another player joined
        - player_left: A player left
        - game_started: Game has started
        - game_state: Full game state update
        - action_result: Result of an action
        - valid_actions: List of valid actions
        - error: Error message
        - pong: Response to ping
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from fastapi import WebSocket, WebSocketDisconnect
from broadcaster import Broadcast
from pydantic import Field, field_serializer, computed_field

from app.game.engine import get_engine
from app.models.game import GameState, GameConfiguration, GameBaseModel
from app.game.actions import create_action
from app.game.enums import GameStatus


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class PlayerConnection:
    """Represents a connected player (kept as dataclass - not serialized)."""
    player_id: str
    name: str
    websocket: WebSocket
    game_id: Optional[str] = None


class GameRoom(GameBaseModel):
    """
    Represents a game room/lobby.
    
    Uses Pydantic for automatic serialization via model_dump().
    """
    room_id: str
    host_id: str
    state: Optional[GameState] = None
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
        return self.player1_id is not None and self.player2_id is not None
    
    @computed_field
    @property
    def is_started(self) -> bool:
        return self.state is not None and self.state.status != GameStatus.WAITING
    
    @computed_field
    @property
    def players(self) -> list[Optional[dict]]:
        """List of players for serialization."""
        return [
            {"player_id": self.player1_id, "name": self.player1_name}
            if self.player1_id else None,
            {"player_id": self.player2_id, "name": self.player2_name}
            if self.player2_id else None,
        ]
    
    def add_player(self, player_id: str, name: str, deck: list[dict]) -> int:
        """Add a player to the room. Returns slot number (1 or 2)."""
        if self.player1_id is None:
            self.player1_id = player_id
            self.player1_name = name
            self.player1_deck = deck
            return 1
        elif self.player2_id is None:
            self.player2_id = player_id
            self.player2_name = name
            self.player2_deck = deck
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
        ids = []
        if self.player1_id:
            ids.append(self.player1_id)
        if self.player2_id:
            ids.append(self.player2_id)
        return ids


def serialize_events(events) -> list[dict[str, Any]]:
    """Serialize a list of game events using Pydantic's model_dump()."""
    return [event.model_dump(mode='json') for event in events]


# ============================================================================
# Game Manager
# ============================================================================

class GameManager:
    """
    Manages game rooms, connections, and message routing.
    
    Uses broadcaster for pub/sub to support multiple server instances.
    """
    
    def __init__(self, broadcast: Broadcast):
        self.broadcast = broadcast
        self.connections: dict[str, PlayerConnection] = {}  # player_id -> connection
        self.rooms: dict[str, GameRoom] = {}  # room_id -> room
        self.player_rooms: dict[str, str] = {}  # player_id -> room_id
    
    # ========================================================================
    # Connection Management
    # ========================================================================
    
    async def connect(self, websocket: WebSocket, player_id: str, name: str) -> PlayerConnection:
        """Register a new player connection."""
        await websocket.accept()
        
        # Disconnect existing connection if any
        if player_id in self.connections:
            await self.disconnect(player_id)
        
        connection = PlayerConnection(
            player_id=player_id,
            name=name,
            websocket=websocket,
        )
        self.connections[player_id] = connection
        return connection
    
    async def disconnect(self, player_id: str) -> None:
        """Disconnect a player and clean up."""
        if player_id not in self.connections:
            return
        
        connection = self.connections[player_id]
        
        # Leave any game room
        if player_id in self.player_rooms:
            room_id = self.player_rooms[player_id]
            await self._leave_room(player_id, room_id)
        
        # Remove connection
        del self.connections[player_id]
        
        try:
            await connection.websocket.close()
        except Exception:
            pass
    
    # ========================================================================
    # Room Management
    # ========================================================================
    
    async def create_room(self, player_id: str, name: str, deck: list[dict]) -> GameRoom:
        """Create a new game room."""
        room = GameRoom(
            room_id=str(uuid4()),
            host_id=player_id,
        )
        room.add_player(player_id, name, deck)
        
        self.rooms[room.room_id] = room
        self.player_rooms[player_id] = room.room_id
        
        if player_id in self.connections:
            self.connections[player_id].game_id = room.room_id
        
        return room
    
    async def join_room(self, player_id: str, name: str, room_id: str, deck: list[dict]) -> GameRoom:
        """Join an existing game room."""
        if room_id not in self.rooms:
            raise ValueError("Room not found")
        
        room = self.rooms[room_id]
        
        if room.is_full:
            raise ValueError("Room is full")
        
        if room.is_started:
            raise ValueError("Game already started")
        
        room.add_player(player_id, name, deck)
        self.player_rooms[player_id] = room_id
        
        if player_id in self.connections:
            self.connections[player_id].game_id = room_id
        
        # Notify other players
        await self._broadcast_to_room(room_id, {
            "type": "player_joined",
            "data": {
                "player_id": player_id,
                "name": name,
                "room": room.model_dump(mode='json'),
            },
        }, exclude=player_id)
        
        return room
    
    async def _leave_room(self, player_id: str, room_id: str) -> None:
        """Internal method to leave a room."""
        if room_id not in self.rooms:
            return
        
        room = self.rooms[room_id]
        room.remove_player(player_id)
        
        if player_id in self.player_rooms:
            del self.player_rooms[player_id]
        
        if player_id in self.connections:
            self.connections[player_id].game_id = None
        
        # Notify remaining players
        await self._broadcast_to_room(room_id, {
            "type": "player_left",
            "data": {
                "player_id": player_id,
                "room": room.model_dump(mode='json'),
            },
        })
        
        # Delete room if empty
        if not room.get_player_ids():
            del self.rooms[room_id]
    
    def get_room(self, room_id: str) -> Optional[GameRoom]:
        """Get a room by ID."""
        return self.rooms.get(room_id)
    
    def list_rooms(self) -> list[dict]:
        """List all available (not started) rooms."""
        return [
            room.model_dump(mode='json')
            for room in self.rooms.values()
            if not room.is_started
        ]
    
    # ========================================================================
    # Game Logic
    # ========================================================================
    
    async def start_game(self, player_id: str, room_id: str) -> dict:
        """Start a game in a room."""
        room = self.get_room(room_id)
        if not room:
            raise ValueError("Room not found")
        
        if room.host_id != player_id:
            raise ValueError("Only the host can start the game")
        
        if not room.is_full:
            raise ValueError("Need 2 players to start")
        
        if room.is_started:
            raise ValueError("Game already started")
        
        # Create the game
        engine = get_engine()
        
        state = engine.create_game(
            player1_id=room.player1_id,
            player1_name=room.player1_name,
            player2_id=room.player2_id,
            player2_name=room.player2_name,
            player1_deck=room.player1_deck,
            player2_deck=room.player2_deck,
        )
        
        # Start the game
        result = engine.start_game(state)
        
        if not result.success:
            raise ValueError(result.error or "Failed to start game")
        
        room.state = result.state
        
        response = {
            "success": True,
            "game_state": result.state.model_dump(mode='json'),
            "events": serialize_events(result.events),
        }
        
        # Broadcast to all players in room
        await self._broadcast_to_room(room_id, {
            "type": "game_started",
            "data": response,
        })
        
        return response
    
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
        
        action_params = self._extract_action_params(action_type, action_data)
        action = create_action(action_type, player_id=player_id, **action_params)
        
        # Process action
        engine = get_engine()
        result = engine.process_action(room.state, action)
        
        if result.success and result.state:
            room.state = result.state
        
        response = {
            "success": result.success,
            "error": result.error,
            "events": serialize_events(result.events),
            "game_over": result.game_over,
            "winner_id": result.winner_id,
            "game_state": result.state.model_dump(mode='json') if result.state else None,
        }
        
        # Broadcast result to all players
        await self._broadcast_to_room(room_id, {
            "type": "action_result",
            "data": response,
        })
        
        return response
    
    def _extract_action_params(self, action_type: str, data: dict) -> dict:
        """Extract action parameters from request data."""
        params = {}
        
        if action_type == "draw":
            params["count"] = data.get("count", 1)
        elif action_type == "play_card":
            params["card_id"] = data.get("card_id")
        elif action_type == "multi_play_card":
            params["card_ids"] = data.get("card_ids", [])
        elif action_type == "promote":
            params["card_id"] = data.get("card_id")
        elif action_type == "swap":
            params["supporting_card_id"] = data.get("supporting_card_id")
            params["attacking_card_id"] = data.get("attacking_card_id")
        elif action_type == "multi_swap":
            params["swaps"] = data.get("swaps", [])
        elif action_type == "associate":
            params["association_card_id"] = data.get("association_card_id")
            params["target_card_id"] = data.get("target_id")
        elif action_type == "evolve":
            params["evolution_card_id"] = data.get("evolution_card_id")
            params["target_card_id"] = data.get("target_id")
        elif action_type == "attack":
            params["attacker_id"] = data.get("attacker_id")
            params["attack_id"] = data.get("attack_id")
            params["target_id"] = data.get("target_id", "")
        elif action_type == "force_defend":
            params["card_id"] = data.get("card_id")
        
        return params
    
    def get_valid_actions(self, player_id: str, room_id: str) -> list[dict]:
        """Get valid actions for a player."""
        room = self.get_room(room_id)
        if not room or not room.state:
            return []
        
        if player_id not in room.get_player_ids():
            return []
        
        engine = get_engine()
        return engine.get_valid_actions(room.state, player_id)
    
    def get_game_state(self, room_id: str) -> Optional[dict]:
        """Get current game state."""
        room = self.get_room(room_id)
        if not room or not room.state:
            return None
        return room.state.model_dump(mode='json')
    
    # ========================================================================
    # Messaging
    # ========================================================================
    
    async def send_to_player(self, player_id: str, message: dict) -> bool:
        """Send a message to a specific player."""
        if player_id not in self.connections:
            return False
        
        try:
            await self.connections[player_id].websocket.send_json(message)
            return True
        except Exception:
            return False
    
    async def _broadcast_to_room(
        self, 
        room_id: str, 
        message: dict, 
        exclude: Optional[str] = None
    ) -> None:
        """Broadcast a message to all players in a room."""
        room = self.get_room(room_id)
        if not room:
            return
        
        for player_id in room.get_player_ids():
            if player_id != exclude:
                await self.send_to_player(player_id, message)
    
    # ========================================================================
    # Message Handler
    # ========================================================================
    
    async def handle_message(self, player_id: str, message: dict) -> None:
        """Handle an incoming WebSocket message."""
        msg_type = message.get("type")
        data = message.get("data", {})
        
        try:
            if msg_type == "create_game":
                room = await self.create_room(
                    player_id=player_id,
                    name=data.get("name", "Player"),
                    deck=data.get("deck", []),
                )
                await self.send_to_player(player_id, {
                    "type": "game_created",
                    "data": {"room": room.model_dump(mode='json')},
                })
            
            elif msg_type == "join_game":
                room = await self.join_room(
                    player_id=player_id,
                    name=data.get("name", "Player"),
                    room_id=data.get("room_id"),
                    deck=data.get("deck", []),
                )
                await self.send_to_player(player_id, {
                    "type": "game_joined",
                    "data": {"room": room.model_dump(mode='json')},
                })
            
            elif msg_type == "list_rooms":
                rooms = self.list_rooms()
                await self.send_to_player(player_id, {
                    "type": "rooms_list",
                    "data": {"rooms": rooms},
                })
            
            elif msg_type == "start_game":
                room_id = self.player_rooms.get(player_id)
                if not room_id:
                    raise ValueError("Not in a game room")
                await self.start_game(player_id, room_id)
            
            elif msg_type == "action":
                room_id = self.player_rooms.get(player_id)
                if not room_id:
                    raise ValueError("Not in a game")
                await self.process_action(player_id, room_id, data)
            
            elif msg_type == "get_state":
                room_id = self.player_rooms.get(player_id)
                if not room_id:
                    raise ValueError("Not in a game")
                state = self.get_game_state(room_id)
                await self.send_to_player(player_id, {
                    "type": "game_state",
                    "data": {"state": state},
                })
            
            elif msg_type == "get_valid_actions":
                room_id = self.player_rooms.get(player_id)
                if not room_id:
                    raise ValueError("Not in a game")
                actions = self.get_valid_actions(player_id, room_id)
                await self.send_to_player(player_id, {
                    "type": "valid_actions",
                    "data": {"actions": actions},
                })
            
            elif msg_type == "leave_game":
                room_id = self.player_rooms.get(player_id)
                if room_id:
                    await self._leave_room(player_id, room_id)
                await self.send_to_player(player_id, {
                    "type": "game_left",
                    "data": {},
                })
            
            elif msg_type == "ping":
                await self.send_to_player(player_id, {"type": "pong"})
            
            else:
                await self.send_to_player(player_id, {
                    "type": "error",
                    "data": {"message": f"Unknown message type: {msg_type}"},
                })
        
        except ValueError as e:
            await self.send_to_player(player_id, {
                "type": "error",
                "data": {"message": str(e)},
            })
        except Exception as e:
            await self.send_to_player(player_id, {
                "type": "error",
                "data": {"message": f"Internal error: {str(e)}"},
            })


# ============================================================================
# WebSocket Handler
# ============================================================================

async def game_websocket_handler(
    websocket: WebSocket, 
    player_id: str, 
    name: str,
    manager: GameManager
) -> None:
    """
    Main WebSocket handler for game connections.
    
    Args:
        websocket: The WebSocket connection
        player_id: Unique identifier for the player
        name: Display name for the player
        manager: The game manager instance
    """
    connection = await manager.connect(websocket, player_id, name)
    
    # Send welcome message
    await manager.send_to_player(player_id, {
        "type": "connected",
        "data": {
            "player_id": player_id,
            "name": name,
            "message": "Connected to game server",
        },
    })
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            await manager.handle_message(player_id, data)
    
    except WebSocketDisconnect:
        await manager.disconnect(player_id)
    except Exception:
        await manager.disconnect(player_id)
