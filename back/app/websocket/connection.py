import asyncio
from fastapi import WebSocket
from starlette.websockets import WebSocketState
from broadcaster import Broadcast

from app.websocket.models import PlayerConnection, PlayerState


class ConnectionManager:
    def __init__(self, broadcast: Broadcast):
        self.broadcast = broadcast

        self.connections: dict[str, PlayerConnection] = {}
        self.tasks: dict[str, asyncio.Task] = {}
        self.channels: dict[str, set[str]] = {}

    async def connect(self, websocket: WebSocket, player: PlayerState) -> PlayerConnection:
        await websocket.accept()

        # Ensure clean slate
        await self.disconnect(player.player_id)

        conn = PlayerConnection(
            player_id=player.player_id,
            websocket=websocket,
        )

        self.connections[player.player_id] = conn
        self.channels[player.player_id] = {f"player:{player.player_id}"}

        self.tasks[player.player_id] = asyncio.create_task(
            self._player_loop(player.player_id)
        )

        return conn

    async def _player_loop(self, player_id: str):
        conn = self.connections.get(player_id)
        if not conn:
            return

        channels = self.channels.get(player_id, set()).copy()
        if not channels:
            return

        try:
            async with self.broadcast.subscribe(channels=channels) as subscriber:
                async for event in subscriber:
                    if player_id not in self.connections:
                        break

                    if conn.websocket.client_state != WebSocketState.CONNECTED:
                        break

                    await conn.websocket.send_json(event.message)

        except asyncio.CancelledError:
            raise
        except Exception:
            # TODO: add logging
            pass

    async def _restart_player_task(self, player_id: str):
        task = self.tasks.get(player_id)
        if task:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)

        if player_id not in self.connections:
            return

        self.tasks[player_id] = asyncio.create_task(
            self._player_loop(player_id)
        )

    async def subscribe_to_room(self, player_id: str, room_id: str):
        if player_id not in self.channels:
            return

        self.channels[player_id].add(f"room:{room_id}")
        await self._restart_player_task(player_id)

    async def unsubscribe_from_room(self, player_id: str, room_id: str):
        if player_id not in self.channels:
            return

        self.channels[player_id].discard(f"room:{room_id}")
        await self._restart_player_task(player_id)

    async def disconnect(self, player_id: str):
        task = self.tasks.pop(player_id, None)
        if task:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)

        conn = self.connections.pop(player_id, None)
        self.channels.pop(player_id, None)

        if conn and conn.websocket.client_state == WebSocketState.CONNECTED:
            await conn.websocket.close()

    def get_connection(self, player_id: str) -> PlayerConnection | None:
        return self.connections.get(player_id)
