"""
WebSocket Message Handler

Handles incoming WebSocket messages and routes them to appropriate handlers.
"""

import logging
from pydantic import ValidationError

from app.websocket.connection import ConnectionManager
from app.websocket.room import RoomManager
from app.websocket.game_logic import GameLogicManager
from app.websocket.messaging import MessageBroadcaster
from app.models.schemas.websocket.client import (
    CreateGameMessage,
    JoinGameMessage,
    ListRoomsMessage,
    StartGameMessage,
    ActionMessage,
    GetStateMessage,
    GetValidActionsMessage,
    LeaveGameMessage,
    PingMessage,
)
from app.models.schemas.websocket.server import (
    GameCreatedMessage,
    GameCreatedData,
    GameJoinedMessage,
    GameJoinedData,
    RoomsListMessage,
    RoomsListData,
    GameStateMessage,
    GameStateData,
    ValidActionsMessage,
    ValidActionsData,
    GameLeftMessage,
    ErrorMessage,
    ErrorData,
    PongMessage,
)

logger = logging.getLogger(__name__)


class MessageHandler:
    """Handles incoming WebSocket messages."""
    
    def __init__(
        self,
        connection_manager: ConnectionManager,
        room_manager: RoomManager,
        game_logic_manager: GameLogicManager,
        message_broadcaster: MessageBroadcaster,
    ):
        self.connection_manager = connection_manager
        self.room_manager = room_manager
        self.game_logic_manager = game_logic_manager
        self.message_broadcaster = message_broadcaster
    
    async def handle_message(self, player_id: str, message: dict) -> None:
        """Handle an incoming WebSocket message."""
        # Validate message structure using Pydantic models
        msg_type = message.get("type")
        data = message.get("data", {})
        
        # Map message types to their Pydantic models for validation
        message_validators = {
            CreateGameMessage.type: CreateGameMessage,
            JoinGameMessage.type: JoinGameMessage,
            ListRoomsMessage.type: ListRoomsMessage,
            StartGameMessage.type: StartGameMessage,
            ActionMessage.type: ActionMessage,
            GetStateMessage.type: GetStateMessage,
            GetValidActionsMessage.type: GetValidActionsMessage,
            LeaveGameMessage.type: LeaveGameMessage,
            PingMessage.type: PingMessage,
        }
        
        # Validate message if we have a validator for it
        if msg_type in message_validators:
            try:
                message_validators[msg_type].model_validate(message)
            except ValidationError as e:
                # Log validation error but continue processing (for backwards compatibility)
                logger.warning(f"WebSocket message validation failed for player {player_id}: {e}")
                # Still send error to client
                await self.message_broadcaster.send_to_player(player_id, ErrorMessage(
                    data=ErrorData(message=f"Invalid message format: {str(e)}")
                ))
                return
        
        try:
            if msg_type == CreateGameMessage.type:
                room = await self.room_manager.create_room(player_id=player_id)
                await self.message_broadcaster.send_to_player(player_id, GameCreatedMessage(
                    data=GameCreatedData(room=room.model_dump(mode='json'))
                ))
            
            elif msg_type == JoinGameMessage.type:
                room = await self.room_manager.join_room(
                    player_id=player_id,
                    room_id=data.get("room_id"),
                )
                await self.message_broadcaster.send_to_player(player_id, GameJoinedMessage(
                    data=GameJoinedData(room=room.model_dump(mode='json'))
                ))
            
            elif msg_type == ListRoomsMessage.type:
                rooms = self.room_manager.list_rooms()
                await self.message_broadcaster.send_to_player(player_id, RoomsListMessage(
                    data=RoomsListData(rooms=rooms)
                ))
            
            elif msg_type == StartGameMessage.type:
                room_id = self.room_manager.get_player_room(player_id)
                if not room_id:
                    raise ValueError("Not in a game room")
                await self.game_logic_manager.start_game(player_id, room_id)
            
            elif msg_type == ActionMessage.type:
                room_id = self.room_manager.get_player_room(player_id)
                if not room_id:
                    raise ValueError("Not in a game")
                await self.game_logic_manager.process_action(player_id, room_id, data)
            
            elif msg_type == GetStateMessage.type:
                room_id = self.room_manager.get_player_room(player_id)
                if not room_id:
                    raise ValueError("Not in a game")
                state = self.game_logic_manager.get_game_state(room_id)
                await self.message_broadcaster.send_to_player(player_id, GameStateMessage(
                    data=GameStateData(state=state)
                ))
            
            elif msg_type == GetValidActionsMessage.type:
                room_id = self.room_manager.get_player_room(player_id)
                if not room_id:
                    raise ValueError("Not in a game")
                actions = self.game_logic_manager.get_valid_actions(player_id, room_id)
                await self.message_broadcaster.send_to_player(player_id, ValidActionsMessage(
                    data=ValidActionsData(actions=actions)
                ))
            
            elif msg_type == LeaveGameMessage.type:
                room_id = self.room_manager.get_player_room(player_id)
                if room_id:
                    await self.room_manager.leave_room(player_id, room_id)
                await self.message_broadcaster.send_to_player(player_id, GameLeftMessage())
            
            elif msg_type == PingMessage.type:
                await self.message_broadcaster.send_to_player(player_id, PongMessage())
            
            else:
                await self.message_broadcaster.send_to_player(player_id, ErrorMessage(
                    data=ErrorData(message=f"Unknown message type: {msg_type}")
                ))
        
        except ValueError as e:
            await self.message_broadcaster.send_to_player(player_id, ErrorMessage(
                data=ErrorData(message=str(e))
            ))
        except Exception as e:
            await self.message_broadcaster.send_to_player(player_id, ErrorMessage(
                data=ErrorData(message=f"Internal error: {str(e)}")
            ))

