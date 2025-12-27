from contextlib import asynccontextmanager

from broadcaster import Broadcast
from fastapi import FastAPI

from app.websocket import GameManager
from app.settings.config import get_settings

settings = get_settings()
broadcast = Broadcast(settings.broadcast_url)
game_manager: GameManager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global game_manager

    await broadcast.connect()
    game_manager = GameManager(broadcast)

    yield

    await broadcast.disconnect()
