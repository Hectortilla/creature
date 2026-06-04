from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.settings.config import get_settings
from app.websocket.connections import PlayerConnections
from app.websocket.game_runner import GameRunner
from app.websocket.lobby import Lobby
from app.websocket.message_router import MessageRouter
from app.websocket.room_registry import RoomRegistry
from app.websocket.session import GameSession

settings = get_settings()

connections: PlayerConnections | None = None
registry: RoomRegistry | None = None
lobby: Lobby | None = None
game_runner: GameRunner | None = None
message_router: MessageRouter | None = None
game_session: GameSession | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global connections, registry, lobby, game_runner, message_router, game_session

    connections = PlayerConnections()
    await connections.async_init()
    registry = RoomRegistry(connections)
    lobby = Lobby(connections, registry)
    game_runner = GameRunner(lobby, registry)
    message_router = MessageRouter(connections, lobby, game_runner)
    game_session = GameSession(connections, lobby, game_runner, message_router)

    yield

    await connections.async_deinit()
