import asyncio
import logging
from fastapi import WebSocket
from starlette.websockets import WebSocketState
from broadcaster import Broadcast

from app.websocket.models import PlayerState
from app.models.schemas.websocket.server import ConnectedData, ConnectedMessage


logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self, broadcast: Broadcast):
        self.broadcast = broadcast
        self.connections: dict[str, WebSocket] = {}

        self.player_tasks: dict[str, asyncio.Task] = {}
        self.channels: dict[str, set[str]] = {}
        self.player_ready: dict[str, asyncio.Event] = {}

    async def connect(self, websocket: WebSocket, player: PlayerState) -> None:
        await websocket.accept()

        self.connections[player.player_id] = websocket

        self.channels[player.player_id] = {f"player:{player.player_id}"}

        ready = asyncio.Event()
        self.player_ready[player.player_id] = ready

        self.player_tasks[player.player_id] = asyncio.create_task(
            self._player_loop(player.player_id)
        )
    
        await ready.wait()

        await websocket.send_json(ConnectedMessage(
            data=ConnectedData(
                player_id=player.player_id,
                name=player.name,
                message="Connected to game server",
            )
        ).model_dump(mode='json'))

    async def _player_loop(self, player_id: str):
        channels = self.channels.get(player_id, set()).copy()
        if not channels:
            return

        queue: asyncio.Queue = asyncio.Queue()
        ready_event = self.player_ready[player_id]

        async def subscribe(channel: str):
            try:
                async with self.broadcast.subscribe(channel=channel) as subscriber:
                    async for event in subscriber:
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
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue

                await self.connections[player_id].send_json(message)

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

        self.channels.pop(player_id, None)
        self.connections.pop(player_id, None)