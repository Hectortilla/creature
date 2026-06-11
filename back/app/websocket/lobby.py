"""
Lobby

Manages game rooms before and around a match: create, join, leave, and list.
Owns the in-memory GameRoom objects; delegates membership and broadcasts to the
RoomRegistry, and direct replies to PlayerConnections.
"""

import traceback
from typing import TYPE_CHECKING
from uuid import uuid4

from app.models.game.room import GameRoom, RoomSummary
from app.models.schemas.websocket.server import (
    ErrorData,
    ErrorMessage,
    GameJoinedData,
    GameJoinedMessage,
    PlayerJoinedData,
    PlayerJoinedMessage,
    PlayerLeftData,
    PlayerLeftMessage,
)
from app.websocket.connections import PlayerConnections
from app.websocket.room_registry import RoomRegistry

if TYPE_CHECKING:
    from app.models.game.player import PlayerState


class Lobby:
    """Room lifecycle: create, join, leave, and list game rooms."""

    def __init__(self, connections: PlayerConnections, registry: RoomRegistry):
        self.connections = connections
        self.registry = registry
        self.rooms: dict[str, GameRoom] = {}

    async def create_room(self, player: "PlayerState") -> GameRoom:
        """Create a new room with the player as host."""
        room = GameRoom(
            room_id=str(uuid4()),
            host_id=player.player_id,
        )
        room.add_player(player)
        self.rooms[room.room_id] = room

        # Redis last: a failed in-memory seat must not leave a dangling player entry.
        await self.registry.add(player.player_id, room.room_id)

        return room

    async def join_room(self, player: "PlayerState", room_id: str) -> GameRoom | None:
        """Join an existing room."""
        if room_id not in self.rooms:
            await self._send_join_error(player.player_id)
            return None

        room = self.rooms[room_id]

        if not room.can_join:
            await self._send_join_error(player.player_id)
            return None

        # Redis last: if two joiners race, add_player raises and the loser stays out of Redis.
        room.add_player(player)
        await self.registry.add(player.player_id, room_id)

        await self.connections.send_to_player(player.player_id, GameJoinedMessage(data=GameJoinedData(room=room)))

        await self.registry.send_to_room(
            room_id,
            PlayerJoinedMessage(
                data=PlayerJoinedData(
                    player_id=player.player_id,
                    name=player.name,
                    room=room,
                )
            ),
        )

        return room

    async def leave_room(self, player_id: str, room_id: str) -> None:
        """Leave a room; always drops Redis membership, even with no in-memory seat."""
        await self.registry.remove(player_id, room_id)

        room = self.rooms.get(room_id)
        if not room:
            return

        if player_id in room.players:
            room.remove_player(player_id)

        await self.registry.send_to_room(
            room_id,
            PlayerLeftMessage(
                data=PlayerLeftData(
                    player_id=player_id,
                    room=room,
                )
            ),
        )

        if not room.get_player_ids():
            self.rooms.pop(room_id, None)

    def get_room(self, room_id: str) -> GameRoom | None:
        """Get a room by ID."""
        return self.rooms.get(room_id)

    async def get_player_room(self, player_id: str) -> str | None:
        """Get the room ID for a player."""
        return await self.registry.room_of(player_id)

    def list_rooms(self) -> list[GameRoom]:
        """List all live rooms."""
        return list(self.rooms.values())

    def list_room_summaries(self) -> list[RoomSummary]:
        """Public room summaries for the lobby listing — never exposes hands or zones."""
        return [room.to_summary() for room in self.list_rooms()]

    async def _send_join_error(self, player_id: str) -> None:
        """Send a join error to a player."""
        await self.connections.send_to_player(
            player_id, ErrorMessage(data=ErrorData(message=f"Failed to join room:\n{traceback.format_exc()}"))
        )
