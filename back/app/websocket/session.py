"""
Game Session

Drives a single player's connection from accept to close: connect, join or
create a room, pump incoming messages through the MessageRouter, then clean up.
"""

import logging
import traceback

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState

from app.models.game.player import PlayerState
from app.websocket.connections import PlayerConnections
from app.websocket.game_runner import GameRunner
from app.websocket.lobby import Lobby
from app.websocket.message_router import MessageRouter

logger = logging.getLogger(__name__)


class GameSession:
    """Manages one WebSocket connection's lifecycle for a game."""

    def __init__(
        self,
        connections: PlayerConnections,
        lobby: Lobby,
        game_runner: GameRunner,
        router: MessageRouter,
    ):
        self.connections = connections
        self.lobby = lobby
        self.game_runner = game_runner
        self.router = router

    async def run(
        self,
        websocket: WebSocket,
        player: PlayerState,
        room_id: str | None = None,
    ) -> None:
        """
        Run the player's connection lifecycle:
        1. Connect and authenticate
        2. Join or create a room
        3. Process incoming messages
        4. Handle disconnection and cleanup
        """
        await self.connections.connect(websocket, player)

        if room_id:
            room = await self.lobby.join_room(player, room_id)
            if room is None:
                return
        else:
            room = await self.lobby.create_room(player)

        # Joining can complete a room (e.g. the second player), so start then.
        if room.game_ready_to_start():
            await self.game_runner.start_game(room)

        try:
            while True:
                data = await websocket.receive_json()
                await self.router.handle_message(player.player_id, data)
        except WebSocketDisconnect:
            pass
        except Exception:
            logger.exception(f"Error in game session: {traceback.format_exc()}")
        finally:
            current_room = await self.lobby.get_player_room(player.player_id)
            if current_room:
                await self.lobby.leave_room(player.player_id, current_room)
            await self.connections.disconnect(player.player_id, websocket)

            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.close()
