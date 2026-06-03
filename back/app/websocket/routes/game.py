"""
WebSocket Game Routes

Actual WebSocket endpoint and connection handler for game connections.
"""

import logging
import traceback
from typing import TYPE_CHECKING

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, WebSocketException, status
from fastapi.websockets import WebSocketState

from app.auth.dependencies import WebSocketUser
from app.database import get_db_session
from app.services.player_state import build_player_state

if TYPE_CHECKING:
    from app.models.game.player import PlayerState

logger = logging.getLogger(__name__)

router = APIRouter()


async def game_websocket_handler(
    websocket: WebSocket,
    player: "PlayerState",
    room_id: str | None = None,
) -> None:
    """
    Main WebSocket handler for game connections.

    Manages the player's connection lifecycle:
    1. Connect and authenticate
    2. Join or create a room
    3. Process incoming messages
    4. Handle disconnection and cleanup
    """
    from app.settings.lifespan import connection_manager, message_handler, room_manager

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
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception(f"Error in game_websocket_handler: {traceback.format_exc()}")
    finally:
        room_id = room_manager.get_player_room(player.player_id)
        if room_id:
            await room_manager.leave_room(player.player_id, room_id)
        await connection_manager.disconnect(player.player_id, websocket)

        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.close()


@router.websocket("/ws")
async def game_websocket(
    websocket: WebSocket,
    user: WebSocketUser,
    deck_id: int = Query(..., description="Deck ID to use for the game"),
    room_id: str = Query(None, description="Optional room ID to join an existing room"),
):
    """
    Authenticated WebSocket endpoint for game connections.

    Connect with: ws://host/game/ws?token=<jwt_token>&deck_id=<deck_id>[&room_id=<room_id>]

    If room_id is provided, the player will automatically join that room after connecting.
    If room_id is not provided, a new room will be created.
    """
    try:
        db = next(get_db_session())
        player = build_player_state(db, user, deck_id)
    except Exception:
        db.close()
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason=traceback.format_exc(),
        ) from None
    finally:
        db.close()

    await game_websocket_handler(websocket, player, room_id=room_id)


@router.get("/rooms")
def list_rooms():
    """
    List all available game rooms (HTTP endpoint for convenience).

    Returns rooms that haven't started yet.
    """
    from app.settings.lifespan import room_manager

    rooms = room_manager.list_rooms() if room_manager else []
    return {"rooms": [room.model_dump(mode="json") for room in rooms]}
