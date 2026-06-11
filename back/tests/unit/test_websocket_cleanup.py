"""Cleanup-path regression tests for the WebSocket session lifecycle.

Injected collaborators are stubbed in memory and async methods driven via
``asyncio.run`` (no Redis, no async pytest plugin).
"""

import asyncio

import pytest
from fastapi.websockets import WebSocketDisconnect, WebSocketState

from app.models.game.player import PlayerState
from app.models.game.room import GameRoom
from app.websocket.lobby import Lobby
from app.websocket.session import GameSession

pytestmark = pytest.mark.unit


def player(player_id: str, *, deck: list | None = None) -> PlayerState:
    return PlayerState(player_id=player_id, name=player_id.upper(), deck=deck)


class FakeRegistry:
    """Records membership calls in memory instead of hitting Redis."""

    def __init__(self) -> None:
        self.added: list[tuple[str, str]] = []
        self.removed: list[tuple[str, str]] = []
        self.broadcasts: list[str] = []

    async def add(self, player_id: str, room_id: str) -> None:
        self.added.append((player_id, room_id))

    async def remove(self, player_id: str, room_id: str) -> None:
        self.removed.append((player_id, room_id))

    async def send_to_room(self, room_id: str, message: object) -> None:
        self.broadcasts.append(room_id)


class FakeConnections:
    def __init__(self) -> None:
        self.connected: list[str] = []
        self.disconnected: list[str] = []

    async def connect(self, websocket: object, p: PlayerState) -> None:
        self.connected.append(p.player_id)

    async def disconnect(self, player_id: str, websocket: object = None) -> None:
        self.disconnected.append(player_id)

    async def send_to_player(self, player_id: str, message: object) -> None:
        pass


def make_lobby() -> Lobby:
    return Lobby(FakeConnections(), FakeRegistry())


def test_join_room_failed_seat_does_not_record_membership():
    """A failed in-memory seat records no Redis membership."""
    lobby = make_lobby()
    room = GameRoom(room_id="r1", host_id="host")
    room.add_player(player("host", deck=[]))
    lobby.rooms["r1"] = room

    with pytest.raises(ValueError):
        asyncio.run(lobby.join_room(player("loser", deck=None), "r1"))

    assert lobby.registry.added == []


def test_leave_room_drops_redis_membership_without_in_memory_seat():
    """leave_room drops Redis membership and never raises without an in-memory seat."""
    lobby = make_lobby()
    room = GameRoom(room_id="r1", host_id="host")
    room.add_player(player("host", deck=[]))
    lobby.rooms["r1"] = room

    asyncio.run(lobby.leave_room("ghost", "r1"))

    assert ("ghost", "r1") in lobby.registry.removed
    assert "r1" in lobby.rooms
    assert "host" in room.players


class FakeWebSocket:
    def __init__(self, frames: list[dict] | None = None) -> None:
        self._frames = list(frames or [])
        self.client_state = WebSocketState.CONNECTED
        self.closed = False

    async def receive_json(self) -> dict:
        if self._frames:
            return self._frames.pop(0)
        raise WebSocketDisconnect()

    async def close(self) -> None:
        self.closed = True


class RaisingJoinLobby:
    async def join_room(self, p: PlayerState, room_id: str) -> GameRoom:
        raise RuntimeError("join blew up")

    async def get_player_room(self, player_id: str) -> str | None:
        return None

    async def leave_room(self, player_id: str, room_id: str) -> None:  # pragma: no cover
        raise AssertionError("should not leave a room that was never joined")


def test_session_cleans_up_when_join_raises():
    """A join that raises still disconnects and closes the socket."""
    connections = FakeConnections()
    session = GameSession(connections, RaisingJoinLobby(), game_runner=None, router=None)
    websocket = FakeWebSocket()

    asyncio.run(session.run(websocket, player("p1", deck=[]), room_id="r1"))

    assert connections.disconnected == ["p1"]
    assert websocket.closed is True


class LeaveRaisingLobby:
    async def create_room(self, p: PlayerState) -> GameRoom:
        room = GameRoom(room_id="r1", host_id=p.player_id)
        room.add_player(p)
        return room

    async def get_player_room(self, player_id: str) -> str | None:
        return "r1"

    async def leave_room(self, player_id: str, room_id: str) -> None:
        raise RuntimeError("redis down during leave")


def test_session_closes_socket_when_leave_room_raises():
    """An exception inside leave_room still tears down the connection and socket."""
    connections = FakeConnections()
    session = GameSession(connections, LeaveRaisingLobby(), game_runner=None, router=None)
    websocket = FakeWebSocket()

    asyncio.run(session.run(websocket, player("p1", deck=[])))

    assert connections.disconnected == ["p1"]
    assert websocket.closed is True
