"""
Room Registry

The single source of truth for room membership (which players are in which
room), backed by Redis so it works across processes, and the one place that
fans a message out to everyone in a room.
"""

import asyncio
import logging
from collections.abc import Callable

from redis import asyncio as redis

from app.models.schemas.websocket import WebSocketMessage
from app.settings.config import get_settings
from app.websocket.connections import PlayerConnections

settings = get_settings()

logger = logging.getLogger(__name__)


class RoomRegistry:
    """Records room membership in Redis and broadcasts to a room's players."""

    def __init__(self, connections: PlayerConnections):
        self.connections = connections
        assert settings.redis_url, "redis_url must be set for the RoomRegistry"
        self.redis = redis.Redis.from_url(settings.redis_url)

    async def add(self, player_id: str, room_id: str) -> None:
        """Record that a player is a member of a room."""
        await self.redis.sadd(f"room:{room_id}", player_id)
        await self.redis.sadd(f"player:{player_id}", room_id)

    async def remove(self, player_id: str, room_id: str) -> None:
        """Drop a player's membership of a room."""
        await self.redis.srem(f"room:{room_id}", player_id)
        await self.redis.srem(f"player:{player_id}", room_id)

    async def players_in(self, room_id: str) -> set[str]:
        """Return the IDs of every player currently in a room."""
        return {pid.decode() for pid in await self.redis.smembers(f"room:{room_id}")}

    async def room_of(self, player_id: str) -> str | None:
        """Return the room a player is in, if any (a player is in at most one)."""
        rooms = await self.redis.smembers(f"player:{player_id}")
        if not rooms:
            return None
        if len(rooms) > 1:
            # Membership must be single; log the breach and pick deterministically.
            logger.warning("Player %s is a member of multiple rooms: %s", player_id, rooms)
        return min(rooms).decode()

    async def send_to_room(self, room_id: str, message: WebSocketMessage) -> None:
        """Send the same message to every player in a room."""
        players = await self.players_in(room_id)
        await asyncio.gather(*[self.connections.send_to_player(player_id, message) for player_id in players])

    async def send_to_each(self, room_id: str, build: Callable[[str], WebSocketMessage]) -> None:
        """Send a per-player message to every player in a room.

        ``build`` is called once per player ID to produce that player's message
        (used for game updates where each player sees a different view).
        """
        players = await self.players_in(room_id)
        await asyncio.gather(*[self.connections.send_to_player(player_id, build(player_id)) for player_id in players])
