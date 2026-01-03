"""
WebSocket Game System

Modular WebSocket-based game communication system.
Handles game creation, player connections, actions, and real-time state updates.
"""

from typing import TYPE_CHECKING

from app.websocket.models import PlayerConnection, GameRoom
from app.websocket.connection import ConnectionManager
from app.websocket.room import RoomManager
from app.websocket.handler import MessageHandler
from app.websocket.messaging import MessageBroadcaster
from app.websocket.serialization import serialize_deck_for_game, serialize_events

if TYPE_CHECKING:
    from app.models.game.player import PlayerState


# WebSocket handler function
async def game_websocket_handler(
    websocket,
    player: "PlayerState",
    connection_manager: ConnectionManager,
    room_manager: RoomManager,
    message_handler: MessageHandler,
    message_broadcaster: MessageBroadcaster,
    room_id: str | None = None,
) -> None:
    """
    Main WebSocket handler for game connections.
    
    Args:
        websocket: The WebSocket connection
        player: PlayerState object with player info and deck
        connection_manager: The connection manager instance
        room_manager: The room manager instance
        message_handler: The message handler instance
        message_broadcaster: The message broadcaster instance
        room_id: Optional room ID to auto-join after connection
    """
    from fastapi import WebSocketDisconnect
    from app.models.schemas.websocket.server import ConnectedMessage, ConnectedData, GameJoinedMessage, GameJoinedData
    from app.models.game.player import PlayerState
    
    # Register player in room manager
    room_manager.register_player(player)
    
    connection = await connection_manager.connect(websocket, player)

    # Send welcome message directly to WebSocket (subscription might not be ready yet)
    await websocket.send_json(ConnectedMessage(
        data=ConnectedData(
            player_id=player.player_id,
            name=player.name,
            message="Connected to game server",
        )
    ).model_dump(mode='json'))
    
    # Auto-join room if room_id is provided
    if room_id:
        try:
            room = await room_manager.join_room(player.player_id, room_id)
            # Send game joined message directly to WebSocket (subscription might not be ready yet)
            await websocket.send_json(GameJoinedMessage(
                data=GameJoinedData(room=room.model_dump(mode='json'))
            ).model_dump(mode='json'))
        except Exception as e:
            # If auto-join fails, send error directly to WebSocket
            import traceback
            from app.models.schemas.websocket.server import ErrorMessage, ErrorData

            await websocket.send_json(ErrorMessage(
                data=ErrorData(message=f"Failed to join room:\n{traceback.format_exc()}")
            ).model_dump(mode='json'))
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            await message_handler.handle_message(player.player_id, data)
    
    except WebSocketDisconnect:
        # Leave any game room first
        room_id = room_manager.get_player_room(player.player_id)
        if room_id:
            await room_manager.leave_room(player.player_id, room_id)
        await connection_manager.disconnect(player.player_id)
    except Exception:
        # Leave any game room first
        room_id = room_manager.get_player_room(player.player_id)
        if room_id:
            await room_manager.leave_room(player.player_id, room_id)
        await connection_manager.disconnect(player.player_id)


__all__ = [
    "PlayerConnection",
    "GameRoom",
    "ConnectionManager",
    "RoomManager",
    "MessageHandler",
    "MessageBroadcaster",
    "serialize_deck_for_game",
    "serialize_events",
    "game_websocket_handler",
]

