"""
WebSocket Message Handler

Handles incoming WebSocket messages and routes them to appropriate handlers.
"""

import logging

from pydantic import ValidationError

from app.models.schemas.websocket.client import (
    ActionMessage,
    GetStateMessage,
    GetValidActionsMessage,
    JoinGameMessage,
    LeaveGameMessage,
    ListRoomsMessage,
    PingMessage,
)
from app.models.schemas.websocket.server import (
    ErrorData,
    ErrorMessage,
    GameJoinedData,
    GameJoinedMessage,
    GameLeftMessage,
    GameStateData,
    GameStateMessage,
    PongMessage,
    RoomsListData,
    RoomsListMessage,
    ValidActionsData,
    ValidActionsMessage,
)
from app.websocket.connection import ConnectionManager
from app.websocket.room_manager import RoomManager

logger = logging.getLogger(__name__)


class MessageHandler:
    """Handles incoming WebSocket messages."""

    def __init__(
        self,
        connection_manager: ConnectionManager,
        room_manager: RoomManager,
    ):
        self.connection_manager = connection_manager
        self.room_manager = room_manager

    async def handle_message(self, player_id: str, message: dict) -> None:
        """Handle an incoming WebSocket message."""
        # Validate message structure using Pydantic models
        msg_type = message.get("type")
        data = message.get("data", {})

        # Map message types to their Pydantic models for validation
        message_validators = {
            JoinGameMessage.type: JoinGameMessage,
            ListRoomsMessage.type: ListRoomsMessage,
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
                await self.connection_manager.send_to_player(
                    player_id, ErrorMessage(data=ErrorData(message=f"Invalid message format: {e!s}"))
                )
                return

        try:
            if msg_type == JoinGameMessage.type:
                room = await self.room_manager.join_room(
                    player_id=player_id,
                    room_id=data.get("room_id"),
                )
                await self.connection_manager.send_to_player(
                    player_id, GameJoinedMessage(data=GameJoinedData(room=room.model_dump(mode="json")))
                )

            elif msg_type == ListRoomsMessage.type:
                rooms = self.room_manager.list_rooms()
                await self.connection_manager.send_to_player(
                    player_id, RoomsListMessage(data=RoomsListData(rooms=rooms))
                )

            elif msg_type == ActionMessage.type:
                room_id = self.room_manager.get_player_room(player_id)
                if not room_id:
                    raise ValueError("Not in a game")
                await self.room_manager.process_action(player_id, room_id, data)

            elif msg_type == GetStateMessage.type:
                room_id = self.room_manager.get_player_room(player_id)
                if not room_id:
                    raise ValueError("Not in a game")
                state = self.room_manager.get_game_state(room_id)
                await self.connection_manager.send_to_player(
                    player_id, GameStateMessage(data=GameStateData(state=state))
                )

            elif msg_type == GetValidActionsMessage.type:
                room_id = self.room_manager.get_player_room(player_id)
                if not room_id:
                    raise ValueError("Not in a game")
                actions = self.room_manager.get_valid_actions(player_id, room_id)
                await self.connection_manager.send_to_player(
                    player_id, ValidActionsMessage(data=ValidActionsData(actions=actions))
                )

            elif msg_type == LeaveGameMessage.type:
                room_id = self.room_manager.get_player_room(player_id)
                if room_id:
                    await self.room_manager.leave_room(player_id, room_id)
                await self.connection_manager.send_to_player(player_id, GameLeftMessage())

            elif msg_type == PingMessage.type:
                await self.connection_manager.send_to_player(player_id, PongMessage())

            else:
                await self.connection_manager.send_to_player(
                    player_id, ErrorMessage(data=ErrorData(message=f"Unknown message type: {msg_type}"))
                )

        except ValueError as e:
            await self.connection_manager.send_to_player(player_id, ErrorMessage(data=ErrorData(message=str(e))))
        except Exception as e:
            await self.connection_manager.send_to_player(
                player_id, ErrorMessage(data=ErrorData(message=f"Internal error: {e!s}"))
            )
