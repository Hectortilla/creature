"""
WebSocket Game Routes

Thin FastAPI endpoints for game connections. The connection lifecycle lives in
GameSession; room queries are served by the Lobby (both wired up in lifespan).
"""

import traceback

from fastapi import APIRouter, Query, WebSocket, WebSocketException, status

from app.auth.dependencies import WebSocketUser
from app.database import get_db_session
from app.models.game.room import RoomSummary
from app.services.player_state import build_player_state
from app.settings import lifespan

router = APIRouter()


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

    assert lifespan.game_session is not None
    await lifespan.game_session.run(websocket, player, room_id=room_id)


@router.get("/rooms", response_model=list[RoomSummary])
def list_rooms() -> list[RoomSummary]:
    """List all game rooms as public summaries (no hands, zones, or decks)."""
    assert lifespan.lobby is not None
    return lifespan.lobby.list_room_summaries()
