"""
WebSocket Message Type Definitions

Dummy endpoints for TypeScript SDK generation.
These endpoints are never called directly - they exist solely to expose
WebSocket message schemas in the OpenAPI spec for client code generation.
"""

from fastapi import APIRouter

from app.models.game.attack import AttackDefinition
from app.models.game.card import GameCard
from app.models.game.element import ElementContribution, ElementPool
from app.models.game.enums import CardStatus
from app.models.game.player import PlayerState
from app.models.game.state import GameStateForPlayer
from app.models.game.zone import ZoneState
from app.models.schemas.websocket.client import (
    ActionMessage,
    GetStateMessage,
    GetValidActionsMessage,
    JoinGameMessage,
    LeaveGameMessage,
    ListRoomsMessage,
    PingMessage,
)
from app.models.schemas.websocket.server import (
    ActionResultMessage,
    ConnectedMessage,
    ErrorMessage,
    GameCreatedMessage,
    GameJoinedMessage,
    GameLeftMessage,
    GameStartedMessage,
    GameStateMessage,
    PlayerJoinedMessage,
    PlayerLeftMessage,
    PongMessage,
    RoomsListMessage,
    ValidActionsMessage,
)

router = APIRouter(prefix="/websocket-messages", tags=["WebSocket Messages"])


# ============================================================================
# Client → Server Messages (request types)
# ============================================================================


@router.post("/join-game", response_model=JoinGameMessage, include_in_schema=True)
async def _ws_join_game_type(msg: JoinGameMessage) -> JoinGameMessage:
    """WebSocket message type: join_game (dummy endpoint for type generation)."""
    return msg


@router.post("/list-rooms", response_model=ListRoomsMessage, include_in_schema=True)
async def _ws_list_rooms_type(msg: ListRoomsMessage) -> ListRoomsMessage:
    """WebSocket message type: list_rooms (dummy endpoint for type generation)."""
    return msg


@router.post("/action", response_model=ActionMessage, include_in_schema=True)
async def _ws_action_type(msg: ActionMessage) -> ActionMessage:
    """WebSocket message type: action (dummy endpoint for type generation)."""
    return msg


@router.post("/get-state", response_model=GetStateMessage, include_in_schema=True)
async def _ws_get_state_type(msg: GetStateMessage) -> GetStateMessage:
    """WebSocket message type: get_state (dummy endpoint for type generation)."""
    return msg


@router.post("/get-valid-actions", response_model=GetValidActionsMessage, include_in_schema=True)
async def _ws_get_valid_actions_type(msg: GetValidActionsMessage) -> GetValidActionsMessage:
    """WebSocket message type: get_valid_actions (dummy endpoint for type generation)."""
    return msg


@router.post("/leave-game", response_model=LeaveGameMessage, include_in_schema=True)
async def _ws_leave_game_type(msg: LeaveGameMessage) -> LeaveGameMessage:
    """WebSocket message type: leave_game (dummy endpoint for type generation)."""
    return msg


@router.post("/ping", response_model=PingMessage, include_in_schema=True)
async def _ws_ping_type(msg: PingMessage) -> PingMessage:
    """WebSocket message type: ping (dummy endpoint for type generation)."""
    return msg


# ============================================================================
# Server → Client Messages (response types)
# ============================================================================


@router.get("/connected", response_model=ConnectedMessage, include_in_schema=True)
async def _ws_connected_type() -> ConnectedMessage:
    """WebSocket message type: connected (dummy endpoint for type generation)."""
    return ConnectedMessage()


@router.get("/game-created", response_model=GameCreatedMessage, include_in_schema=True)
async def _ws_game_created_type() -> GameCreatedMessage:
    """WebSocket message type: game_created (dummy endpoint for type generation)."""
    return GameCreatedMessage()


@router.get("/game-joined", response_model=GameJoinedMessage, include_in_schema=True)
async def _ws_game_joined_type() -> GameJoinedMessage:
    """WebSocket message type: game_joined (dummy endpoint for type generation)."""
    return GameJoinedMessage()


@router.get("/player-joined", response_model=PlayerJoinedMessage, include_in_schema=True)
async def _ws_player_joined_type() -> PlayerJoinedMessage:
    """WebSocket message type: player_joined (dummy endpoint for type generation)."""
    return PlayerJoinedMessage()


@router.get("/player-left", response_model=PlayerLeftMessage, include_in_schema=True)
async def _ws_player_left_type() -> PlayerLeftMessage:
    """WebSocket message type: player_left (dummy endpoint for type generation)."""
    return PlayerLeftMessage()


@router.get("/game-started", response_model=GameStartedMessage, include_in_schema=True)
async def _ws_game_started_type() -> GameStartedMessage:
    """WebSocket message type: game_started (dummy endpoint for type generation)."""
    return GameStartedMessage()


@router.get("/game-state", response_model=GameStateMessage, include_in_schema=True)
async def _ws_game_state_type() -> GameStateMessage:
    """WebSocket message type: game_state (dummy endpoint for type generation)."""
    return GameStateMessage()


@router.get("/action-result", response_model=ActionResultMessage, include_in_schema=True)
async def _ws_action_result_type() -> ActionResultMessage:
    """WebSocket message type: action_result (dummy endpoint for type generation)."""
    return ActionResultMessage()


@router.get("/valid-actions", response_model=ValidActionsMessage, include_in_schema=True)
async def _ws_valid_actions_type() -> ValidActionsMessage:
    """WebSocket message type: valid_actions (dummy endpoint for type generation)."""
    return ValidActionsMessage()


@router.get("/rooms-list", response_model=RoomsListMessage, include_in_schema=True)
async def _ws_rooms_list_type() -> RoomsListMessage:
    """WebSocket message type: rooms_list (dummy endpoint for type generation)."""
    return RoomsListMessage()


@router.get("/game-left", response_model=GameLeftMessage, include_in_schema=True)
async def _ws_game_left_type() -> GameLeftMessage:
    """WebSocket message type: game_left (dummy endpoint for type generation)."""
    return GameLeftMessage()


@router.get("/error", response_model=ErrorMessage, include_in_schema=True)
async def _ws_error_type() -> ErrorMessage:
    """WebSocket message type: error (dummy endpoint for type generation)."""
    return ErrorMessage()


@router.get("/pong", response_model=PongMessage, include_in_schema=True)
async def _ws_pong_type() -> PongMessage:
    """WebSocket message type: pong (dummy endpoint for type generation)."""
    return PongMessage()


# ============================================================================
# Game Domain Types (for frontend code generation)
# ============================================================================


@router.get("/domain/element-contribution", response_model=ElementContribution, include_in_schema=True)
async def _domain_element_contribution_type() -> ElementContribution:
    """Game domain type: ElementContribution (for type generation)."""
    ...


@router.get("/domain/element-pool", response_model=ElementPool, include_in_schema=True)
async def _domain_element_pool_type() -> ElementPool:
    """Game domain type: ElementPool (for type generation)."""
    ...


@router.get("/domain/attack-definition", response_model=AttackDefinition, include_in_schema=True)
async def _domain_attack_definition_type() -> AttackDefinition:
    """Game domain type: AttackDefinition (for type generation)."""
    ...


@router.get("/domain/zone-state", response_model=ZoneState, include_in_schema=True)
async def _domain_zone_state_type() -> ZoneState:
    """Game domain type: ZoneState (for type generation)."""
    ...


@router.get("/domain/game-card", response_model=GameCard, include_in_schema=True)
async def _domain_game_card_type() -> GameCard:
    """Game domain type: GameCard (for type generation)."""
    ...


@router.get("/domain/card-status", response_model=CardStatus, include_in_schema=True)
async def _domain_card_status_type() -> CardStatus:
    """Game domain type: CardStatus (for type generation)."""
    ...


@router.get("/domain/player-state", response_model=PlayerState, include_in_schema=True)
async def _domain_player_state_type() -> PlayerState:
    """Game domain type: PlayerState (for type generation)."""
    ...


@router.get("/domain/game-state-for-player", response_model=GameStateForPlayer, include_in_schema=True)
async def _domain_game_state_for_player_type() -> GameStateForPlayer:
    """Game domain type: GameStateForPlayer (for type generation)."""
    ...
