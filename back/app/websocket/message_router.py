"""
Message Router

Validates incoming WebSocket messages and dispatches them to the Lobby or the
GameRunner, sending any direct reply back to the requesting player.
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
    GameLeftMessage,
    GameStateData,
    GameStateMessage,
    PongMessage,
    RoomsListData,
    RoomsListMessage,
    ValidActionsData,
    ValidActionsMessage,
)
from app.websocket.connections import PlayerConnections
from app.websocket.game_runner import GameRunner
from app.websocket.lobby import Lobby

logger = logging.getLogger(__name__)


class MessageRouter:
    """Validates and dispatches incoming WebSocket messages."""

    def __init__(
        self,
        connections: PlayerConnections,
        lobby: Lobby,
        game_runner: GameRunner,
    ):
        self.connections = connections
        self.lobby = lobby
        self.game_runner = game_runner

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
                await self.connections.send_to_player(
                    player_id, ErrorMessage(data=ErrorData(message=f"Invalid message format: {e!s}"))
                )
                return

        try:
            if msg_type == JoinGameMessage.type:
                # A player joins (or creates) their room at connect time via the
                # `room_id` query param. Joining a different room mid-session is
                # not supported: this handler only has a player_id, not the
                # PlayerState (deck, etc.) a join requires.
                await self.connections.send_to_player(
                    player_id,
                    ErrorMessage(
                        data=ErrorData(
                            message="Joining a room mid-session is not supported; reconnect with ?room_id=..."
                        )
                    ),
                )

            elif msg_type == ListRoomsMessage.type:
                rooms = self.lobby.list_room_summaries()
                await self.connections.send_to_player(player_id, RoomsListMessage(data=RoomsListData(rooms=rooms)))

            elif msg_type == ActionMessage.type:
                room_id = await self.lobby.get_player_room(player_id)
                if not room_id:
                    raise ValueError("Not in a game")
                await self.game_runner.process_action(player_id, room_id, data)

            elif msg_type == GetStateMessage.type:
                room_id = await self.lobby.get_player_room(player_id)
                if not room_id:
                    raise ValueError("Not in a game")
                state = self.game_runner.get_game_state(room_id)
                await self.connections.send_to_player(player_id, GameStateMessage(data=GameStateData(state=state)))

            elif msg_type == GetValidActionsMessage.type:
                room_id = await self.lobby.get_player_room(player_id)
                if not room_id:
                    raise ValueError("Not in a game")
                actions = self.game_runner.get_valid_actions(player_id, room_id)
                await self.connections.send_to_player(
                    player_id, ValidActionsMessage(data=ValidActionsData(actions=actions))
                )

            elif msg_type == LeaveGameMessage.type:
                room_id = await self.lobby.get_player_room(player_id)
                if room_id:
                    await self.lobby.leave_room(player_id, room_id)
                await self.connections.send_to_player(player_id, GameLeftMessage())

            elif msg_type == PingMessage.type:
                await self.connections.send_to_player(player_id, PongMessage())

            else:
                await self.connections.send_to_player(
                    player_id, ErrorMessage(data=ErrorData(message=f"Unknown message type: {msg_type}"))
                )

        except ValueError as e:
            await self.connections.send_to_player(player_id, ErrorMessage(data=ErrorData(message=str(e))))
        except Exception as e:
            await self.connections.send_to_player(
                player_id, ErrorMessage(data=ErrorData(message=f"Internal error: {e!s}"))
            )
