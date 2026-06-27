"""
Game Runner

Runs the game engine for a room: starting a match, processing actions, and
answering state/valid-action queries. Reads rooms from the Lobby and fans game
updates out through the RoomRegistry.
"""

import structlog

from app.game.engine import get_engine
from app.models.game.room import GameRoom
from app.models.game.state import GameConfiguration
from app.models.schemas.websocket.server import (
    ActionResultData,
    ActionResultMessage,
    GameStartedData,
    GameStartedMessage,
)
from app.settings.config import get_settings
from app.settings.observability import get_tracer
from app.websocket.lobby import Lobby
from app.websocket.room_registry import RoomRegistry
from app.websocket.serialization import serialize_events, serialize_events_for_player


class GameRunner:
    """
    Drives the engine for a room.

    Responsibilities:
    - Starting games
    - Processing game actions
    - Reporting game state and valid actions
    """

    def __init__(self, lobby: Lobby, registry: RoomRegistry):
        self.lobby = lobby
        self.registry = registry
        # Configured RNG seed (None = system entropy). app.game stays pure — the
        # seed rides in via GameConfiguration rather than app.game reading settings.
        self.engine = get_engine(GameConfiguration(seed=get_settings().game_seed))

    async def start_game(self, room: GameRoom) -> dict:
        """
        Start a game in a room.

        Creates initial game state, sets up decks, and broadcasts to players.
        """
        state = self.engine.create_game(room)
        room.state = state

        result = self.engine.start_game(state)
        assert result.state is not None and result.final_players is not None
        game_state = result.state

        if result.success:
            room.state = game_state
            room.state.room.players = result.final_players

        def build(player_id: str) -> GameStartedMessage:
            return GameStartedMessage(
                data=GameStartedData(
                    success=True,
                    game_state=game_state.serialize_for_player(player_id),
                    events=serialize_events_for_player(result.events, player_id),
                    valid_actions=result.valid_actions,
                )
            )

        await self.registry.send_to_each(room.room_id, build)

        return {
            "success": True,
            "game_state": result.state.model_dump(mode="json") if result.state else None,
            "events": serialize_events(result.events),
        }

    async def process_action(self, player_id: str, room_id: str, action_data: dict) -> dict:
        """Process a game action."""
        room = self.lobby.get_room(room_id)
        if not room:
            raise ValueError("Room not found")

        if not room.state:
            raise ValueError("Game not started")

        if player_id not in room.get_player_ids():
            raise ValueError("Player not in this game")

        with (
            structlog.contextvars.bound_contextvars(room_id=room_id, player_id=player_id, game_id=room.state.game_id),
            get_tracer().start_as_current_span(
                "engine.process_action",
                attributes={
                    "game.room_id": room_id,
                    "game.player_id": player_id,
                    "action.type": str(action_data.get("action_type", "")),
                },
            ),
        ):
            result = self.engine.process_action_from_dict(room.state, player_id, action_data)

        if result.success and result.state:
            room.state = result.state

        def build(pid: str) -> ActionResultMessage:
            return ActionResultMessage(
                data=ActionResultData(
                    success=result.success,
                    error=result.error,
                    events=serialize_events_for_player(result.events, pid),
                    game_over=result.game_over,
                    winner_id=result.winner_id,
                    game_state=result.state.serialize_for_player(pid) if result.state else None,
                    valid_actions=result.valid_actions,
                )
            )

        await self.registry.send_to_each(room_id, build)

        return {
            "success": result.success,
            "error": result.error,
            "events": serialize_events(result.events),
            "game_over": result.game_over,
            "winner_id": result.winner_id,
            "game_state": result.state.model_dump(mode="json") if result.state else None,
        }

    def get_valid_actions(self, player_id: str, room_id: str) -> list[dict]:
        """Get valid actions for a player."""
        room = self.lobby.get_room(room_id)
        if not room or not room.state:
            return []

        if player_id not in room.get_player_ids():
            return []

        return self.engine.get_valid_actions(room.state)

    def get_game_state(self, room_id: str) -> dict | None:
        """Get current game state."""
        room = self.lobby.get_room(room_id)
        if not room or not room.state:
            return None
        return room.state.model_dump(mode="json")
