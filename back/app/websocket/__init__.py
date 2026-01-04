"""
WebSocket Game System

Modular WebSocket-based game communication system.
Handles game creation, player connections, actions, and real-time state updates.
"""

from typing import TYPE_CHECKING
import traceback

from app.models.schemas.websocket.server import ErrorMessage, ErrorData
from app.websocket.connection import ConnectionManager
from app.websocket.room import RoomManager
from app.websocket.handler import MessageHandler

if TYPE_CHECKING:
    from app.models.game.player import PlayerState


# WebSocket handler function
async def game_websocket_handler(
    websocket,
    player: "PlayerState",
    connection_manager: ConnectionManager,
    room_manager: RoomManager,
    message_handler: MessageHandler,
    room_id: str | None = None,
) -> None:
    from app.models.schemas.websocket.server import ConnectedMessage, ConnectedData, GameJoinedMessage, GameJoinedData
    
    room_manager.register_player(player)
    connection = await connection_manager.connect(websocket, player)

    await websocket.send_json(ConnectedMessage(
        data=ConnectedData(
            player_id=player.player_id,
            name=player.name,
            message="Connected to game server",
        )
    ).model_dump(mode='json'))
    
    if room_id:
        try:
            room = await room_manager.join_room(player.player_id, room_id)
            await websocket.send_json(GameJoinedMessage(
                data=GameJoinedData(room=room.model_dump(mode='json'))
            ).model_dump(mode='json'))
        except Exception as e:
            await websocket.send_json(ErrorMessage(
                data=ErrorData(message=f"Failed to join room:\n{traceback.format_exc()}")
            ).model_dump(mode='json'))

    try:
        while True:
            data = await websocket.receive_json()
            await message_handler.handle_message(player.player_id, data)

    except Exception:
        room_id = room_manager.get_player_room(player.player_id)
        if room_id:
            await room_manager.leave_room(player.player_id, room_id)
        await connection_manager.disconnect(player.player_id)

