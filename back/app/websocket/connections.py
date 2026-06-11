"""
Player Connections

Owns the live WebSocket connections and delivers messages to a single player
over Redis pub/sub. Pure transport: it knows nothing about rooms or games.
"""

import asyncio
import json
import logging

from broadcaster import Broadcast
from fastapi import WebSocket

from app.models.game.player import PlayerState
from app.models.schemas.websocket import WebSocketMessage
from app.models.schemas.websocket.server import ConnectedData, ConnectedMessage
from app.settings.config import get_settings

settings = get_settings()

logger = logging.getLogger(__name__)

CHANNEL_PREFIX = settings.channel_namespace


def _player_channel(player_id: str) -> str:
    return f"{CHANNEL_PREFIX}:player:{player_id}"


class PlayerConnections:
    """Tracks open player sockets and pushes messages to them via pub/sub."""

    def __init__(self):
        self.broadcast = Broadcast(settings.broadcast_url)
        self.connections: dict[str, WebSocket] = {}

        self.player_tasks: dict[str, asyncio.Task] = {}
        self.player_ready: dict[str, asyncio.Event] = {}

    async def async_init(self):
        await self.broadcast.connect()

    async def async_deinit(self):
        await self.broadcast.disconnect()

    async def connect(self, websocket: WebSocket, player: PlayerState) -> None:
        await websocket.accept()

        # Cancel any existing player loop from a prior connection to prevent
        # duplicate broadcast subscriptions (which cause duplicate messages).
        old_task = self.player_tasks.pop(player.player_id, None)
        if old_task:
            old_task.cancel()
            await asyncio.gather(old_task, return_exceptions=True)

        self.connections[player.player_id] = websocket

        ready = asyncio.Event()
        self.player_ready[player.player_id] = ready

        self.player_tasks[player.player_id] = asyncio.create_task(self._player_loop(player.player_id))

        await ready.wait()

        await self.send_to_player(
            player.player_id,
            ConnectedMessage(
                data=ConnectedData(
                    player_id=player.player_id,
                    name=player.name,
                    message="Connected to game server",
                )
            ),
        )

    async def _player_loop(self, player_id: str):
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

        subscription_task = asyncio.create_task(subscribe(_player_channel(player_id)))

        await asyncio.sleep(0)
        ready_event.set()

        try:
            while True:
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=1.0)
                except TimeoutError:
                    continue
                try:
                    payload = json.loads(message)
                    logger.info("Sending message to player %s: %s", player_id, payload.get("type") or "")
                    await self.connections[player_id].send_json(payload)
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    logger.exception("Error sending message to player %s: %s", player_id, e)
                    logger.info("WebSocket disconnected for player %s, stopping player loop", player_id)
                    await self.disconnect(player_id)
                    break

        except asyncio.CancelledError:
            raise

        finally:
            subscription_task.cancel()
            await asyncio.gather(subscription_task, return_exceptions=True)

    async def disconnect(self, player_id: str, websocket: WebSocket | None = None):
        # If a specific websocket is provided, only disconnect if it's still the
        # active connection. This prevents a stale handler's finally-block from
        # tearing down a newer reconnection.
        if websocket and self.connections.get(player_id) is not websocket:
            return

        task = self.player_tasks.pop(player_id, None)
        if task and task is not asyncio.current_task():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)

        self.connections.pop(player_id, None)
        self.player_ready.pop(player_id, None)

    async def send_to_player(self, player_id: str, message: WebSocketMessage):
        await self.broadcast.publish(
            channel=_player_channel(player_id),
            message=json.dumps(message.model_dump(mode="json")),
        )
