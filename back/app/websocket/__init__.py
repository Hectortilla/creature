"""
WebSocket Game System

Modular WebSocket-based game communication system.
Handles game creation, player connections, actions, and real-time state updates.
"""

from app.websocket.models import PlayerConnection, GameRoom
from app.websocket.connection import ConnectionManager
from app.websocket.room import RoomManager
from app.websocket.handler import MessageHandler
from app.websocket.messaging import MessageBroadcaster
from app.websocket.serialization import serialize_deck_for_game, serialize_events
from app.websocket.endpoint import handle_websocket_connection, list_game_rooms


# WebSocket handler function
async def game_websocket_handler(
    websocket,
    player_id: str,
    name: str,
    connection_manager: ConnectionManager,
    room_manager: RoomManager,
    message_handler: MessageHandler,
    message_broadcaster: MessageBroadcaster,
    deck: list[dict],
    room_id: str | None = None,
) -> None:
    """
    Main WebSocket handler for game connections.
    
    Args:
        websocket: The WebSocket connection
        player_id: Unique identifier for the player
        name: Display name for the player
        connection_manager: The connection manager instance
        room_manager: The room manager instance
        message_handler: The message handler instance
        message_broadcaster: The message broadcaster instance
        deck: Serialized deck to use for the game
        room_id: Optional room ID to auto-join after connection
    """
    from fastapi import WebSocketDisconnect
    from app.models.schemas.websocket.server import ConnectedMessage, ConnectedData, GameJoinedMessage, GameJoinedData
    
    connection = await connection_manager.connect(websocket, player_id, name, deck)
    
    # Send welcome message
    await message_broadcaster.send_to_player(player_id, ConnectedMessage(
        data=ConnectedData(
            player_id=player_id,
            name=name,
            message="Connected to game server",
        )
    ))
    
    # Auto-join room if room_id is provided
    if room_id:
        try:
            room = await room_manager.join_room(player_id, room_id)
            # Send game joined message
            await message_broadcaster.send_to_player(player_id, GameJoinedMessage(
                data=GameJoinedData(room=room.model_dump(mode='json'))
            ))
        except Exception as e:
            # If auto-join fails, send error but don't disconnect
            from app.models.schemas.websocket.server import ErrorMessage, ErrorData
            await message_broadcaster.send_to_player(player_id, ErrorMessage(
                data=ErrorData(message=f"Failed to join room: {str(e)}")
            ))
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            await message_handler.handle_message(player_id, data)
    
    except WebSocketDisconnect:
        # Leave any game room first
        room_id = room_manager.get_player_room(player_id)
        if room_id:
            await room_manager.leave_room(player_id, room_id)
        await connection_manager.disconnect(player_id)
    except Exception:
        # Leave any game room first
        room_id = room_manager.get_player_room(player_id)
        if room_id:
            await room_manager.leave_room(player_id, room_id)
        await connection_manager.disconnect(player_id)


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
    "handle_websocket_connection",
    "list_game_rooms",
]

