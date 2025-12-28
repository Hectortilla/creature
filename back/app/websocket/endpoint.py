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
from app.websocket.serialization import serialize_deck_for_game


async def handle_websocket_connection(
    websocket: WebSocket,
    user: WebSocketUser,
    deck_id: int,
    connection_manager: ConnectionManager,
    room_manager: RoomManager,
) -> None:
    """
    Handle WebSocket connection with validation.
    
    Validates:
    - Deck exists and belongs to the user
    - Deck is valid for playing (correct size)
    - Player doesn't have another active game
    """
    player_id = str(user.id)
    name = user.full_name or user.username
    
    # Get database session
    db = next(get_db_session())
    try:
        # Check if player already has an active game
        from app.settings.lifespan import game_manager as gm
        if gm and connection_manager.has_connection(player_id):
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
        
    finally:
        db.close()
    
    # Pass serialized deck to handler
    # Import here to ensure game_manager is initialized from lifespan
    from app.settings.lifespan import game_manager as gm
    from app.websocket import game_websocket_handler
    if gm is None:
        raise WebSocketException(
            code=status.WS_1011_INTERNAL_ERROR,
            reason="Game manager not initialized",
        )
    await game_websocket_handler(websocket, player_id, name, gm, serialized_deck)


async def list_game_rooms(room_manager: RoomManager) -> dict:
    """
    List all available game rooms (HTTP endpoint for convenience).
    
    Returns rooms that haven't started yet.
    """
    return {"rooms": room_manager.list_rooms()}

