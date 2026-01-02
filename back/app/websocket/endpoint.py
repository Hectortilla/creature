"""
WebSocket Endpoints

HTTP and WebSocket endpoints for game connections.
"""

from fastapi import WebSocket, Query, status, WebSocketException

from app.auth import WebSocketUser
from app.database import get_db_session
from app.models.game.enums import GameStatus
from app.websocket.connection import ConnectionManager
from app.websocket.room import RoomManager
from app.websocket.handler import MessageHandler
from app.websocket.messaging import MessageBroadcaster


async def handle_websocket_connection(
    websocket: WebSocket,
    user: WebSocketUser,
    deck_id: int,
    connection_manager: ConnectionManager,
    room_manager: RoomManager,
    message_handler: MessageHandler,
    message_broadcaster: MessageBroadcaster,
    room_id: str | None = None,
) -> None:
    """
    Handle WebSocket connection with validation.
    
    Validates:
    - Deck exists and belongs to the user
    - Deck is valid for playing (correct size)
    - Player doesn't have another active game
    - If room_id is provided, room exists and can be joined
    
    If room_id is provided, automatically joins the room after connection.
    """
    # Get database session
    db = next(get_db_session())
    try:
        # Check if player already has an active game
        player_id = str(user.id)
        if connection_manager.has_connection(player_id):
            existing_connection = connection_manager.get_connection(player_id)
            if existing_connection and existing_connection.game_id:
                # Check if the game is still active
                room = room_manager.get_room(existing_connection.game_id)
                if room:
                    # If game has started and is not finished, refuse connection
                    if room.state and room.state.status != GameStatus.FINISHED:
                        raise WebSocketException(
                            code=status.WS_1008_POLICY_VIOLATION,
                            reason="Player already has an active game",
                        )
                    # If game hasn't started but room exists, also refuse (player is in a waiting room)
                    elif not room.state:
                        raise WebSocketException(
                            code=status.WS_1008_POLICY_VIOLATION,
                            reason="Player already has an active game",
                        )
        
        # Create player state from user (fetches, validates, and serializes deck)
        try:
            player = user.to_player_state(deck_id, db)
        except ValueError as e:
            raise WebSocketException(
                code=status.WS_1008_POLICY_VIOLATION,
                reason=str(e),
            )
        
        # Validate room_id if provided
        if room_id:
            room = room_manager.get_room(room_id)
            if not room:
                raise WebSocketException(
                    code=status.WS_1008_POLICY_VIOLATION,
                    reason="Room not found",
                )
            if not room.can_join:
                raise WebSocketException(
                    code=status.WS_1008_POLICY_VIOLATION,
                    reason="Room cannot be joined. Room must have exactly 1 player and game must not have started.",
                )
    
    finally:
        db.close()
    
    # Pass player to handler
    from app.websocket import game_websocket_handler
    await game_websocket_handler(
        websocket, 
        player,
        connection_manager,
        room_manager,
        message_handler,
        message_broadcaster,
        room_id=room_id
    )
