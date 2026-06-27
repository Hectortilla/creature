"""Query/dispatch tests for ``GameRunner`` with a stubbed engine/lobby/registry.

No Redis: the engine is replaced with a fake and the per-player fan-out
(``RoomRegistry.send_to_each``) is recorded in memory.
"""

import asyncio
import types

import pytest

from app.models.game.state import GameStateForPlayer
from app.models.schemas.websocket.server import ActionResultMessage, GameStartedMessage
from app.websocket.game_runner import GameRunner

pytestmark = pytest.mark.unit


class FakeState:
    """Stands in for the engine's ``GameState`` — only what GameRunner touches."""

    def __init__(self) -> None:
        self.game_id = "g1"
        self.room = types.SimpleNamespace(players={})

    def serialize_for_player(self, player_id: str) -> GameStateForPlayer:
        return GameStateForPlayer(game_id=self.game_id)

    def model_dump(self, mode: str = "json") -> dict:
        return {"game_id": self.game_id}


class FakeResult:
    def __init__(self, *, state: FakeState | None) -> None:
        self.success = True
        self.state = state
        self.error: str | None = None
        self.final_players: dict = {}
        self.events: list = []
        self.game_over = False
        self.winner_id = None
        self.valid_actions: list = []


class FakeEngine:
    def __init__(self, result: FakeResult) -> None:
        self._result = result

    def create_game(self, room: object) -> FakeState | None:
        return self._result.state

    def start_game(self, state: object) -> FakeResult:
        return self._result

    def process_action_from_dict(self, state: object, player_id: str, action_data: dict) -> FakeResult:
        return self._result

    def get_valid_actions(self, state: object) -> list[dict]:
        return [{"action_type": "draw"}]


class FakeRegistry:
    def __init__(self, players: tuple[str, ...] = ("p1", "p2")) -> None:
        self._players = list(players)
        self.calls: list[tuple[str, list]] = []

    async def send_to_each(self, room_id: str, build) -> None:
        self.calls.append((room_id, [build(pid) for pid in self._players]))


class FakeLobby:
    def __init__(self, room: object | None = None) -> None:
        self._room = room

    def get_room(self, room_id: str) -> object | None:
        return self._room


class FakeRoom:
    def __init__(self, *, room_id: str = "r1", players: tuple[str, ...] = ("p1", "p2"), state: object = None) -> None:
        self.room_id = room_id
        self._players = list(players)
        self.state = state

    def get_player_ids(self) -> list[str]:
        return self._players


def make_runner(*, lobby: FakeLobby, registry: FakeRegistry, engine: FakeEngine) -> GameRunner:
    runner = GameRunner(lobby, registry)
    runner.engine = engine
    return runner


def test_start_game_broadcasts_started_message_per_player():
    result = FakeResult(state=FakeState())
    registry = FakeRegistry(players=("p1", "p2"))
    runner = make_runner(lobby=FakeLobby(), registry=registry, engine=FakeEngine(result))
    room = FakeRoom(room_id="r1")

    out = asyncio.run(runner.start_game(room))

    room_id, messages = registry.calls[0]
    assert room_id == "r1"
    assert len(messages) == 2
    assert all(isinstance(m, GameStartedMessage) for m in messages)
    assert room.state is result.state
    assert out["success"] is True
    assert out["game_state"] == {"game_id": "g1"}


def test_process_action_broadcasts_result_per_player_and_updates_state():
    result = FakeResult(state=FakeState())
    registry = FakeRegistry(players=("p1", "p2"))
    room = FakeRoom(room_id="r1", players=("p1", "p2"), state=FakeState())
    runner = make_runner(lobby=FakeLobby(room), registry=registry, engine=FakeEngine(result))

    out = asyncio.run(runner.process_action("p1", "r1", {"action_type": "draw"}))

    room_id, messages = registry.calls[0]
    assert room_id == "r1"
    assert len(messages) == 2
    assert all(isinstance(m, ActionResultMessage) for m in messages)
    assert room.state is result.state
    assert out["success"] is True


def test_process_action_raises_when_room_missing():
    runner = make_runner(lobby=FakeLobby(None), registry=FakeRegistry(), engine=FakeEngine(FakeResult(state=None)))
    with pytest.raises(ValueError, match="Room not found"):
        asyncio.run(runner.process_action("p1", "r1", {"action_type": "draw"}))


def test_process_action_raises_when_game_not_started():
    room = FakeRoom(state=None)
    runner = make_runner(lobby=FakeLobby(room), registry=FakeRegistry(), engine=FakeEngine(FakeResult(state=None)))
    with pytest.raises(ValueError, match="Game not started"):
        asyncio.run(runner.process_action("p1", "r1", {"action_type": "draw"}))


def test_process_action_raises_when_player_not_in_game():
    room = FakeRoom(players=("p2",), state=FakeState())
    runner = make_runner(lobby=FakeLobby(room), registry=FakeRegistry(), engine=FakeEngine(FakeResult(state=None)))
    with pytest.raises(ValueError, match="Player not in this game"):
        asyncio.run(runner.process_action("p1", "r1", {"action_type": "draw"}))


def test_get_valid_actions_returns_engine_actions():
    room = FakeRoom(players=("p1",), state=FakeState())
    runner = make_runner(lobby=FakeLobby(room), registry=FakeRegistry(), engine=FakeEngine(FakeResult(state=None)))
    assert runner.get_valid_actions("p1", "r1") == [{"action_type": "draw"}]


def test_get_valid_actions_empty_when_no_room():
    runner = make_runner(lobby=FakeLobby(None), registry=FakeRegistry(), engine=FakeEngine(FakeResult(state=None)))
    assert runner.get_valid_actions("p1", "r1") == []


def test_get_valid_actions_empty_when_player_not_in_game():
    room = FakeRoom(players=("p2",), state=FakeState())
    runner = make_runner(lobby=FakeLobby(room), registry=FakeRegistry(), engine=FakeEngine(FakeResult(state=None)))
    assert runner.get_valid_actions("p1", "r1") == []


def test_get_game_state_returns_serialized_state():
    room = FakeRoom(state=FakeState())
    runner = make_runner(lobby=FakeLobby(room), registry=FakeRegistry(), engine=FakeEngine(FakeResult(state=None)))
    assert runner.get_game_state("r1") == {"game_id": "g1"}


def test_get_game_state_none_when_no_room():
    runner = make_runner(lobby=FakeLobby(None), registry=FakeRegistry(), engine=FakeEngine(FakeResult(state=None)))
    assert runner.get_game_state("r1") is None
