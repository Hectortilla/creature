from contextlib import asynccontextmanager
from typing import Optional

from broadcaster import Broadcast
from fastapi import FastAPI

from app.websocket.connection import ConnectionManager
from app.websocket.room import RoomManager
from app.websocket.handler import MessageHandler
from app.websocket.messaging import MessageBroadcaster
from app.settings.config import get_settings

settings = get_settings()
broadcast: Optional[Broadcast] = None
connection_manager: Optional[ConnectionManager] = None
room_manager: Optional[RoomManager] = None
message_handler: Optional[MessageHandler] = None
message_broadcaster: Optional[MessageBroadcaster] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global broadcast, connection_manager, room_manager, message_handler, message_broadcaster

    broadcast = Broadcast(settings.broadcast_url)
    await broadcast.connect()
    
    connection_manager = ConnectionManager(broadcast)
    message_broadcaster = MessageBroadcaster(broadcast)
    room_manager = RoomManager(connection_manager, message_broadcaster)
    message_handler = MessageHandler(connection_manager, room_manager, message_broadcaster)

    yield

    await broadcast.disconnect()
