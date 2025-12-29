"""
WebSocket Endpoints

HTTP and WebSocket endpoints for game connections.
"""

from fastapi import WebSocket, Query, status, WebSocketException

from app.auth import WebSocketUser
from app.database import get_db_session
from app.services.decks import DeckService
from app.models.game.enums import GameStatus
from app.websocket.connection import ConnectionManager
from app.websocket.room import RoomManager
from app.websocket.handler import MessageHandler
from app.websocket.messaging import MessageBroadcaster
from app.websocket.serialization import serialize_deck_for_game


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
    player_id = str(user.id)
    name = user.full_name or user.username
    
    # Get database session
    db = next(get_db_session())
    try:
        # Check if player already has an active game
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
        
        # Get and validate deck
        deck_service = DeckService(db, user.id)
        deck = deck_service.get_user_deck(deck_id)
        
        if not deck:
            raise WebSocketException(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="Deck not found or does not belong to user",
            )
        
        # Validate deck is valid for playing
        if not deck.is_valid_for_playing(db):
            raise WebSocketException(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="Deck is not valid for playing",
            )
        
        # Serialize deck
        enriched_deck = deck_service.get_enriched(deck_id)
        if not enriched_deck:
            raise WebSocketException(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="Failed to load deck",
            )
        
        serialized_deck = serialize_deck_for_game(enriched_deck.cards)
        
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
    
    # Pass serialized deck to handler
    from app.websocket import game_websocket_handler
    await game_websocket_handler(
        websocket, 
        player_id, 
        name, 
        connection_manager,
        room_manager,
        message_handler,
        message_broadcaster,
        serialized_deck, 
        room_id=room_id
    )


async def list_game_rooms(room_manager: RoomManager) -> dict:
    """
    List all available game rooms (HTTP endpoint for convenience).
    
    Returns rooms that haven't started yet.
    """
    return {"rooms": room_manager.list_rooms()}

