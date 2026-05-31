from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.settings.config import get_settings
from app.websocket.connection import ConnectionManager
from app.websocket.message_handler import MessageHandler
from app.websocket.room_manager import RoomManager

settings = get_settings()
connection_manager: ConnectionManager | None = None
room_manager: RoomManager | None = None
message_handler: MessageHandler | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global connection_manager, room_manager, message_handler

    connection_manager = ConnectionManager()
    await connection_manager.async_init()
    room_manager = RoomManager(connection_manager)
    message_handler = MessageHandler(connection_manager, room_manager)

    yield

    await connection_manager.async_deinit()
