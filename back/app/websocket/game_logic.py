"""
Game Logic

Handles game start, action processing, and state management.
"""

from typing import Optional

from app.game.engine import get_engine
from app.game.actions import create_action
from app.websocket.models import GameRoom
from app.websocket.serialization import serialize_events
from app.websocket.messaging import MessageBroadcaster
from app.models.schemas.websocket.server import (
    GameStartedMessage,
    GameStartedData,
    ActionResultMessage,
    ActionResultData,
)


class GameLogicManager:
    """Manages game logic operations."""
    
    def __init__(self, room_manager, message_broadcaster: MessageBroadcaster):
        self.room_manager = room_manager
        self.message_broadcaster = message_broadcaster
    
    async def start_game(self, player_id: str, room_id: str) -> dict:
        """Start a game in a room."""
        room = self.room_manager.get_room(room_id)
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
        
        # Broadcast to all players in room
        response_data = GameStartedData(
            success=True,
            game_state=result.state.model_dump(mode='json'),
            events=serialize_events(result.events),
            valid_actions=result.valid_actions,
        )
        await self.message_broadcaster.broadcast_to_room(
            room_id,
            GameStartedMessage(data=response_data)
        )
        
        return {
            "success": response_data.success,
            "game_state": response_data.game_state,
            "events": response_data.events,
        }
    
    async def process_action(self, player_id: str, room_id: str, action_data: dict) -> dict:
        """Process a game action."""
        room = self.room_manager.get_room(room_id)
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
        room = self.room_manager.get_room(room_id)
        if not room or not room.state:
            return []
        
        if player_id not in room.get_player_ids():
            return []
        
        engine = get_engine()
        return engine.get_valid_actions(room.state, player_id)
    
    def get_game_state(self, room_id: str) -> Optional[dict]:
        """Get current game state."""
        room = self.room_manager.get_room(room_id)
        if not room or not room.state:
            return None
        return room.state.model_dump(mode='json')

