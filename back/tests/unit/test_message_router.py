"""Routing/dispatch tests for ``MessageRouter`` — the WebSocket trust boundary.

Collaborators are stubbed in memory and async methods driven via ``asyncio.run``
(no Redis, no async pytest plugin), mirroring ``test_websocket_cleanup.py``.
"""

import asyncio

import pytest

from app.models.schemas.websocket.server import (
    ErrorMessage,
    GameLeftMessage,
    GameStateMessage,
    PongMessage,
    RoomsListMessage,
    ValidActionsMessage,
)
from app.websocket.message_router import MessageRouter

pytestmark = pytest.mark.unit


class FakeConnections:
    def __init__(self) -> None:
        self.sent: list[tuple[str, object]] = []

    async def send_to_player(self, player_id: str, message: object) -> None:
        self.sent.append((player_id, message))


class FakeLobby:
    def __init__(self, *, room_id: str | None = None, summaries: list | None = None) -> None:
        self._room_id = room_id
        self._summaries = summaries or []
        self.left: list[tuple[str, str]] = []

    async def get_player_room(self, player_id: str) -> str | None:
        return self._room_id

    def list_room_summaries(self) -> list:
        return self._summaries

    async def leave_room(self, player_id: str, room_id: str) -> None:
        self.left.append((player_id, room_id))


class FakeGameRunner:
    def __init__(self, *, raise_on_state: bool = False) -> None:
        self.actions: list[tuple[str, str, dict]] = []
        self.raise_on_state = raise_on_state

    async def process_action(self, player_id: str, room_id: str, data: dict) -> None:
        self.actions.append((player_id, room_id, data))

    def get_game_state(self, room_id: str) -> dict | None:
        if self.raise_on_state:
            raise RuntimeError("engine exploded")
        return None

    def get_valid_actions(self, player_id: str, room_id: str) -> list[dict]:
        return []


def handle(message: dict, *, lobby: FakeLobby | None = None, runner: FakeGameRunner | None = None) -> list:
    connections = FakeConnections()
    router = MessageRouter(connections, lobby or FakeLobby(), runner or FakeGameRunner())
    asyncio.run(router.handle_message("p1", message))
    return connections.sent


def test_list_rooms_returns_summaries():
    sent = handle({"type": "list_rooms", "data": {}})
    assert isinstance(sent[-1][1], RoomsListMessage)


def test_action_in_room_dispatches_to_runner():
    runner = FakeGameRunner()
    handle(
        {"type": "action", "data": {"action_type": "draw"}},
        lobby=FakeLobby(room_id="r1"),
        runner=runner,
    )
    assert runner.actions == [("p1", "r1", {"action_type": "draw"})]


def test_action_while_not_in_room_sends_error():
    sent = handle({"type": "action", "data": {"action_type": "draw"}}, lobby=FakeLobby(room_id=None))
    message = sent[-1][1]
    assert isinstance(message, ErrorMessage)
    assert message.data.message == "Not in a game"


def test_get_state_sends_game_state():
    sent = handle({"type": "get_state", "data": {}}, lobby=FakeLobby(room_id="r1"))
    assert isinstance(sent[-1][1], GameStateMessage)


def test_get_valid_actions_sends_valid_actions():
    sent = handle({"type": "get_valid_actions", "data": {}}, lobby=FakeLobby(room_id="r1"))
    assert isinstance(sent[-1][1], ValidActionsMessage)


def test_leave_game_leaves_room_and_confirms():
    lobby = FakeLobby(room_id="r1")
    sent = handle({"type": "leave_game", "data": {}}, lobby=lobby)
    assert lobby.left == [("p1", "r1")]
    assert isinstance(sent[-1][1], GameLeftMessage)


def test_leave_game_without_room_still_confirms():
    lobby = FakeLobby(room_id=None)
    sent = handle({"type": "leave_game", "data": {}}, lobby=lobby)
    assert lobby.left == []
    assert isinstance(sent[-1][1], GameLeftMessage)


def test_ping_returns_pong():
    sent = handle({"type": "ping", "data": {}})
    assert isinstance(sent[-1][1], PongMessage)


def test_join_mid_session_is_rejected():
    sent = handle({"type": "join_game", "data": {"room_id": "r1"}})
    message = sent[-1][1]
    assert isinstance(message, ErrorMessage)
    assert "mid-session" in message.data.message


def test_unknown_type_sends_error():
    sent = handle({"type": "bogus", "data": {}})
    message = sent[-1][1]
    assert isinstance(message, ErrorMessage)
    assert "Unknown message type" in message.data.message


def test_malformed_action_data_sends_error_and_survives():
    sent = handle({"type": "action", "data": {}})  # missing required action_type
    message = sent[-1][1]
    assert isinstance(message, ErrorMessage)
    assert "Invalid message format" in message.data.message


def test_internal_error_is_caught_and_reported():
    sent = handle(
        {"type": "get_state", "data": {}},
        lobby=FakeLobby(room_id="r1"),
        runner=FakeGameRunner(raise_on_state=True),
    )
    message = sent[-1][1]
    assert isinstance(message, ErrorMessage)
    assert "Internal error" in message.data.message
