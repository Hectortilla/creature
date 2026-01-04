"""
WebSocket Game System

Modular WebSocket-based game communication system.
Handles game creation, player connections, actions, and real-time state updates.
"""

from typing import TYPE_CHECKING

from fastapi.websockets import WebSocketState

if TYPE_CHECKING:
    from app.models.game.player import PlayerState


# WebSocket handler function
async def game_websocket_handler(
    websocket,
    player: "PlayerState",
    room_id: str | None = None,
) -> None:
    from app.settings.lifespan import connection_manager, room_manager, message_handler

    await connection_manager.connect(websocket, player)
    
    if room_id:
        if not await room_manager.join_room(player, room_id):
            return
    elif not await room_manager.create_room(player):
        return

    try:
        while True:
            data = await websocket.receive_json()
            await message_handler.handle_message(player.player_id, data)

    except Exception as e:
        room_id = room_manager.get_player_room(player.player_id)
        if room_id:
            await room_manager.leave_room(player.player_id, room_id)
        await connection_manager.disconnect(player.player_id)

        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.close()