import asyncio
import logging
from fastapi import WebSocket
from starlette.websockets import WebSocketState
from broadcaster import Broadcast

from app.websocket.models import PlayerConnection, PlayerState


logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self, broadcast: Broadcast):
        self.broadcast = broadcast

        self.connections: dict[str, PlayerConnection] = {}
        self.player_tasks: dict[str, asyncio.Task] = {}
        self.channels: dict[str, set[str]] = {}
        self.player_ready: dict[str, asyncio.Event] = {}

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

        ready = asyncio.Event()
        self.player_ready[player.player_id] = ready

        self.player_tasks[player.player_id] = asyncio.create_task(
            self._player_loop(player.player_id)
        )
    
        await ready.wait()

    async def _player_loop(self, player_id: str):
        """
        Fan-in loop:
        - One subscription task per channel
        - All messages forwarded to the websocket
        """
        conn = self.connections.get(player_id)
        if not conn:
            return

        channels = self.channels.get(player_id, set()).copy()
        if not channels:
            return

        queue: asyncio.Queue = asyncio.Queue()
        ready_event = self.player_ready[player_id]

        async def subscribe(channel: str):
            try:
                async with self.broadcast.subscribe(channel=channel) as subscriber:
                    async for event in subscriber:
                        if player_id not in self.connections:
                            break
                        queue.put_nowait(event.message)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.exception("Error in subscription to channel %s for player %s: %s", channel, player_id, e)

        subscription_tasks = [
            asyncio.create_task(subscribe(channel))
            for channel in channels
        ]

        await asyncio.sleep(0)
        ready_event.set()

        try:
            while True:
                if player_id not in self.connections:
                    break

                if conn.websocket.client_state != WebSocketState.CONNECTED:
                    break

                try:
                    message = await asyncio.wait_for(queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue

                await conn.websocket.send_json(message)

        except asyncio.CancelledError:
            raise

        finally:
            for task in subscription_tasks:
                task.cancel()
            await asyncio.gather(*subscription_tasks, return_exceptions=True)

    async def _restart_player_task(self, player_id: str):
        task = self.player_tasks.get(player_id)
        if task:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)

        ready = asyncio.Event()
        self.player_ready[player_id] = ready

        self.player_tasks[player_id] = asyncio.create_task(
            self._player_loop(player_id)
        )
        await ready.wait()

    async def subscribe_to_room(self, player_id: str, room_id: str):
        self.channels[player_id].add(f"room:{room_id}")
        await self._restart_player_task(player_id)

    async def unsubscribe_from_room(self, player_id: str, room_id: str):
        self.channels[player_id].discard(f"room:{room_id}")
        await self._restart_player_task(player_id)

    async def disconnect(self, player_id: str):
        task = self.player_tasks.pop(player_id, None)
        if task:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)

        conn = self.connections.pop(player_id, None)
        self.channels.pop(player_id, None)

        if conn and conn.websocket.client_state == WebSocketState.CONNECTED:
            await conn.websocket.close()

    def get_connection(self, player_id: str) -> PlayerConnection | None:
        return self.connections.get(player_id)