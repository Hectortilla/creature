"""
Game Router

FastAPI router for game-related endpoints.
Provides REST API for game creation, actions, and state queries.
"""

from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from app.game.engine import get_engine
from app.game.models import GameState
from app.game.actions import create_action, Action
from app.game.enums import Zone, TurnPhase, GameStatus


# ============================================================================
# Request/Response Models
# ============================================================================

class PlayerInfo(BaseModel):
    player_id: str
    name: str


class CardData(BaseModel):
    id: int
    name: str
    health: int = 10
    physical_defence: int = 0
    magic_defence: int = 0
    element_ids: list[int] = Field(default_factory=list)
    element_contribution: list[dict[str, int]] = Field(default_factory=list)
    attacks: list[dict[str, Any]] = Field(default_factory=list)
    skill_ids: list[int] = Field(default_factory=list)
    association_ids: list[int] = Field(default_factory=list)
    is_evolution: bool = False
    evolves_from_id: Optional[int] = None


class CreateGameRequest(BaseModel):
    player1: PlayerInfo
    player2: PlayerInfo
    player1_deck: list[CardData]
    player2_deck: list[CardData]


class ActionRequest(BaseModel):
    player_id: str
    action_type: str
    card_id: Optional[str] = None
    card_ids: Optional[list[str]] = None
    attack_id: Optional[int] = None
    target_id: Optional[str] = None
    attacker_id: Optional[str] = None
    supporting_card_id: Optional[str] = None
    attacking_card_id: Optional[str] = None
    association_card_id: Optional[str] = None
    evolution_card_id: Optional[str] = None
    swaps: Optional[list[tuple[str, str]]] = None
    count: int = 1


class CardStateResponse(BaseModel):
    instance_id: str
    card_id: int
    name: str
    owner_id: str
    current_health: int
    max_health: int
    physical_defense: int
    magical_defense: int
    element_ids: list[int]
    zone: str
    turns_in_zone: int
    can_attack: bool
    can_promote: bool
    has_attacked_this_turn: bool


class ZoneStateResponse(BaseModel):
    zone: str
    card_ids: list[str]
    max_capacity: Optional[int]
    is_full: bool


class PlayerStateResponse(BaseModel):
    player_id: str
    name: str
    turn_count: int
    elements: dict[int, int]
    zones: dict[str, ZoneStateResponse]


class GameStateResponse(BaseModel):
    game_id: str
    status: str
    turn_number: int
    current_phase: str
    active_player_id: Optional[str]
    winner_id: Optional[str]
    players: dict[str, PlayerStateResponse]
    cards: dict[str, CardStateResponse]


class EventResponse(BaseModel):
    event_type: str
    timestamp: str
    data: dict[str, Any]


class ActionResponse(BaseModel):
    success: bool
    error: Optional[str] = None
    events: list[EventResponse] = Field(default_factory=list)
    game_over: bool = False
    winner_id: Optional[str] = None
    game_state: Optional[GameStateResponse] = None


class ValidActionsResponse(BaseModel):
    actions: list[dict[str, Any]]


# ============================================================================
# In-Memory Game Storage (only stores GameState, not engines)
# ============================================================================

class GameStorage:
    """
    Simple in-memory storage for game states.
    
    Only stores GameState - engines are stateless and created on demand.
    In production, replace with database or Redis.
    """
    
    _games: dict[str, GameState] = {}
    
    @classmethod
    def save_game(cls, state: GameState) -> None:
        """Save/update a game state."""
        cls._games[state.game_id] = state
    
    @classmethod
    def get_game(cls, game_id: str) -> Optional[GameState]:
        """Get a game by ID."""
        return cls._games.get(game_id)
    
    @classmethod
    def delete_game(cls, game_id: str) -> bool:
        """Delete a game."""
        if game_id in cls._games:
            del cls._games[game_id]
            return True
        return False
    
    @classmethod
    def list_games(cls) -> list[str]:
        """List all game IDs."""
        return list(cls._games.keys())


# ============================================================================
# Serialization Helpers
# ============================================================================

def serialize_card(card) -> CardStateResponse:
    return CardStateResponse(
        instance_id=card.instance_id,
        card_id=card.card_id,
        name=card.name,
        owner_id=card.owner_id,
        current_health=card.current_health,
        max_health=card.max_health,
        physical_defense=card.physical_defense,
        magical_defense=card.magical_defense,
        element_ids=card.element_ids,
        zone=card.zone.name,
        turns_in_zone=card.turns_in_zone,
        can_attack=card.can_attack(),
        can_promote=card.can_promote(),
        has_attacked_this_turn=card.has_attacked_this_turn,
    )


def serialize_zone(zone_state) -> ZoneStateResponse:
    return ZoneStateResponse(
        zone=zone_state.zone.name,
        card_ids=zone_state.card_ids,
        max_capacity=zone_state.max_capacity,
        is_full=zone_state.is_full(),
    )


def serialize_player(player) -> PlayerStateResponse:
    return PlayerStateResponse(
        player_id=player.player_id,
        name=player.name,
        turn_count=player.turn_count,
        elements=dict(player.element_pool.elements),
        zones={
            zone.name: serialize_zone(zone_state)
            for zone, zone_state in player.zones.items()
        },
    )


def serialize_game_state(state: GameState) -> GameStateResponse:
    return GameStateResponse(
        game_id=state.game_id,
        status=state.status.name,
        turn_number=state.turn_number,
        current_phase=state.current_phase.name,
        active_player_id=state.active_player_id,
        winner_id=state.winner_id,
        players={
            pid: serialize_player(player)
            for pid, player in state.players.items()
        },
        cards={
            cid: serialize_card(card)
            for cid, card in state.cards.items()
        },
    )


def serialize_events(events) -> list[EventResponse]:
    return [
        EventResponse(
            event_type=event.event_type,
            timestamp=event.timestamp.isoformat(),
            data=event.to_dict(),
        )
        for event in events
    ]


def build_action(request: ActionRequest) -> Action:
    """Build an Action from request parameters."""
    params = {"player_id": request.player_id}
    
    if request.action_type == "draw":
        params["count"] = request.count
    elif request.action_type == "play_card":
        params["card_id"] = request.card_id
    elif request.action_type == "multi_play_card":
        params["card_ids"] = request.card_ids or []
    elif request.action_type == "promote":
        params["card_id"] = request.card_id
    elif request.action_type == "swap":
        params["supporting_card_id"] = request.supporting_card_id
        params["attacking_card_id"] = request.attacking_card_id
    elif request.action_type == "multi_swap":
        params["swaps"] = request.swaps or []
    elif request.action_type == "associate":
        params["association_card_id"] = request.association_card_id
        params["target_card_id"] = request.target_id
    elif request.action_type == "evolve":
        params["evolution_card_id"] = request.evolution_card_id
        params["target_card_id"] = request.target_id
    elif request.action_type == "attack":
        params["attacker_id"] = request.attacker_id
        params["attack_id"] = request.attack_id
        params["target_id"] = request.target_id or ""
    elif request.action_type == "force_defend":
        params["card_id"] = request.card_id
    
    return create_action(request.action_type, **params)


# ============================================================================
# Router
# ============================================================================

router = APIRouter(prefix="/game", tags=["game"])


@router.post("/create", response_model=GameStateResponse)
async def create_game(request: CreateGameRequest):
    """Create a new game."""
    engine = get_engine()
    deck_size = engine.config.deck_size
    
    player1_deck = [card.model_dump() for card in request.player1_deck]
    player2_deck = [card.model_dump() for card in request.player2_deck]
    
    if len(player1_deck) != deck_size:
        raise HTTPException(
            status_code=400,
            detail=f"Player 1 deck must have exactly {deck_size} cards (has {len(player1_deck)})"
        )
    if len(player2_deck) != deck_size:
        raise HTTPException(
            status_code=400,
            detail=f"Player 2 deck must have exactly {deck_size} cards (has {len(player2_deck)})"
        )
    
    state = engine.create_game(
        player1_id=request.player1.player_id,
        player1_name=request.player1.name,
        player2_id=request.player2.player_id,
        player2_name=request.player2.name,
        player1_deck=player1_deck,
        player2_deck=player2_deck,
    )
    
    GameStorage.save_game(state)
    return serialize_game_state(state)


@router.post("/{game_id}/start", response_model=ActionResponse)
async def start_game(game_id: str, first_player_id: Optional[str] = None):
    """Start a game."""
    state = GameStorage.get_game(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Game not found")
    
    if state.status != GameStatus.STARTING:
        raise HTTPException(
            status_code=400,
            detail=f"Game cannot be started (status: {state.status.name})"
        )
    
    engine = get_engine()
    result = engine.start_game(state, first_player_id)
    
    if result.success and result.state:
        GameStorage.save_game(result.state)
    
    return ActionResponse(
        success=result.success,
        error=result.error,
        events=serialize_events(result.events),
        game_over=result.game_over,
        winner_id=result.winner_id,
        game_state=serialize_game_state(result.state) if result.state else None,
    )


@router.post("/{game_id}/action", response_model=ActionResponse)
async def perform_action(game_id: str, request: ActionRequest):
    """Perform a game action."""
    state = GameStorage.get_game(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Game not found")
    
    try:
        action = build_action(request)
        engine = get_engine()
        result = engine.process_action(state, action)
        
        # Save the new state
        if result.success and result.state:
            GameStorage.save_game(result.state)
        
        return ActionResponse(
            success=result.success,
            error=result.error,
            events=serialize_events(result.events),
            game_over=result.game_over,
            winner_id=result.winner_id,
            game_state=serialize_game_state(result.state) if result.state else None,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{game_id}", response_model=GameStateResponse)
async def get_game(game_id: str):
    """Get the current state of a game."""
    state = GameStorage.get_game(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Game not found")
    return serialize_game_state(state)


@router.get("/{game_id}/valid-actions", response_model=ValidActionsResponse)
async def get_valid_actions(game_id: str, player_id: str):
    """Get all valid actions for a player in the current state."""
    state = GameStorage.get_game(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Game not found")
    
    if player_id not in state.players:
        raise HTTPException(status_code=400, detail="Player not in this game")
    
    engine = get_engine()
    actions = engine.get_valid_actions(state, player_id)
    return ValidActionsResponse(actions=actions)


@router.get("/{game_id}/events", response_model=list[EventResponse])
async def get_events(game_id: str, since_turn: Optional[int] = None, limit: int = 50):
    """Get game events, optionally filtered by turn."""
    state = GameStorage.get_game(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Game not found")
    
    events = state.event_log
    if since_turn is not None:
        events = [e for e in events if e.get("turn", 0) >= since_turn]
    events = events[-limit:]
    
    return [
        EventResponse(
            event_type=e.get("event_type", "unknown"),
            timestamp=e.get("timestamp", ""),
            data=e,
        )
        for e in events
    ]


@router.delete("/{game_id}")
async def delete_game(game_id: str):
    """Delete a game."""
    if not GameStorage.delete_game(game_id):
        raise HTTPException(status_code=404, detail="Game not found")
    return {"message": "Game deleted"}


@router.get("/", response_model=list[str])
async def list_games():
    """List all active game IDs."""
    return GameStorage.list_games()


# ============================================================================
# WebSocket for Real-Time Updates
# ============================================================================

class GameConnectionManager:
    """Manages WebSocket connections for game updates."""
    
    def __init__(self):
        self.connections: dict[str, list[tuple[str, WebSocket]]] = {}
    
    async def connect(self, game_id: str, player_id: str, websocket: WebSocket):
        await websocket.accept()
        if game_id not in self.connections:
            self.connections[game_id] = []
        self.connections[game_id].append((player_id, websocket))
    
    def disconnect(self, game_id: str, websocket: WebSocket):
        if game_id in self.connections:
            self.connections[game_id] = [
                (pid, ws) for pid, ws in self.connections[game_id]
                if ws != websocket
            ]
            if not self.connections[game_id]:
                del self.connections[game_id]
    
    async def broadcast_to_game(self, game_id: str, message: dict):
        if game_id in self.connections:
            for _, websocket in self.connections[game_id]:
                try:
                    await websocket.send_json(message)
                except Exception:
                    pass


game_manager = GameConnectionManager()


@router.websocket("/{game_id}/ws/{player_id}")
async def game_websocket(websocket: WebSocket, game_id: str, player_id: str):
    """WebSocket endpoint for real-time game updates."""
    state = GameStorage.get_game(game_id)
    
    if not state:
        await websocket.close(code=4004, reason="Game not found")
        return
    
    if player_id not in state.players:
        await websocket.close(code=4003, reason="Player not in game")
        return
    
    await game_manager.connect(game_id, player_id, websocket)
    
    try:
        # Send initial state
        await websocket.send_json({
            "type": "state",
            "data": serialize_game_state(state).model_dump(),
        })
        
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "action":
                # Re-fetch state (may have changed)
                state = GameStorage.get_game(game_id)
                if not state:
                    await websocket.send_json({
                        "type": "error",
                        "data": {"message": "Game not found"},
                    })
                    continue
                
                try:
                    request = ActionRequest(**data.get("data", {}), player_id=player_id)
                    action = build_action(request)
                    engine = get_engine()
                    result = engine.process_action(state, action)
                    
                    if result.success and result.state:
                        GameStorage.save_game(result.state)
                        state = result.state
                    
                    response = ActionResponse(
                        success=result.success,
                        error=result.error,
                        events=serialize_events(result.events),
                        game_over=result.game_over,
                        winner_id=result.winner_id,
                        game_state=serialize_game_state(result.state) if result.state else None,
                    )
                    
                    await game_manager.broadcast_to_game(game_id, {
                        "type": "action_result",
                        "data": response.model_dump(),
                    })
                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "data": {"message": str(e)},
                    })
            
            elif data.get("type") == "get_valid_actions":
                state = GameStorage.get_game(game_id)
                if state:
                    engine = get_engine()
                    actions = engine.get_valid_actions(state, player_id)
                    await websocket.send_json({
                        "type": "valid_actions",
                        "data": {"actions": actions},
                    })
            
            elif data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        game_manager.disconnect(game_id, websocket)
    except Exception:
        game_manager.disconnect(game_id, websocket)


# Export router
game_router = router
