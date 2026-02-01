from contextlib import asynccontextmanager
from typing import Optional

from broadcaster import Broadcast
from fastapi import FastAPI

from app.websocket.connection import ConnectionManager
from app.websocket.room import RoomManager
from app.websocket.handler import MessageHandler
from app.settings.config import get_settings

settings = get_settings()
connection_manager: Optional[ConnectionManager] = None
room_manager: Optional[RoomManager] = None
message_handler: Optional[MessageHandler] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global connection_manager, room_manager, message_handler

    connection_manager = ConnectionManager()
    await connection_manager.async_init()
    room_manager = RoomManager(connection_manager)
    message_handler = MessageHandler(connection_manager, room_manager)

    yield

    await connection_manager.async_deinit()
