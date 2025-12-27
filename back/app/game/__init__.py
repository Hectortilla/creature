"""
Creature Card Game Engine

Event-driven game engine with clean architecture:
    Action → Validator → Evaluator → Events → EventLoop → Reducer → New State

All models use Pydantic BaseModel with model_dump() for serialization.
Use @computed_field for derived properties that should be included in output.

Modules:
- enums: Game enumerations (zones, phases, damage types)
- actions: Player action definitions (intent only, no computation)
- events: Game events with computed data
- event_generator: ActionToEventGenerator - transforms actions into events
- event_loop: Processes events, triggers effects
- reducer: Pure functions that apply events to state
- effects: Effect/skill system
- elements: Element interaction matrix
- validators: Rule validation
- engine: Orchestrates the pipeline
- router: FastAPI endpoints

Game state models are located in app.models.game:
    from app.models.game import (
        GameBaseModel, GameCard, PlayerState, ZoneState, GameState,
        ElementContribution, AttackDefinition, AttackResult,
        GameConfiguration, ElementPool
    )

Usage:
    from app.game import get_engine
    from app.models.game import GameState
    from app.game.actions import PlayCardAction
    
    engine = get_engine()
    state = engine.create_game(...)
    result = engine.start_game(state)
    state = result.state
    
    # Serialize using Pydantic's model_dump()
    state_dict = state.model_dump(mode='json')
"""

from app.models.game import (
    Zone,
    TurnPhase,
    DamageType,
    GameStatus,
    CardStatus,
    EffectTiming,
)
from app.game.actions import (
    Action,
    DrawAction,
    PlayCardAction,
    PromoteAction,
    SwapAction,
    AssociationAction,
    EvolutionAction,
    AttackAction,
    PassPhaseAction,
    ForceDefendAction,
    ConcedeAction,
    MultiPlayCardAction,
    MultiSwapAction,
    create_action,
)
from app.models.game import (
    GameEvent,
    CardDrawnEvent,
    CardMovedEvent,
    CardPlayedEvent,
    CardPromotedEvent,
    CardSwappedEvent,
    CardAssociatedEvent,
    CardEvolvedEvent,
    AttackDeclaredEvent,
    DamageDealtEvent,
    CardDestroyedEvent,
    ElementsConsumedEvent,
    ElementsRestoredEvent,
    TurnStartedEvent,
    TurnEndedEvent,
    PhaseChangedEvent,
    GameStartedEvent,
    GameEndedEvent,
    NoDefenderEvent,
    EffectTriggeredEvent,
    EffectAppliedEvent,
)
from app.game.effects import (
    Effect,
    EffectTrigger,
    EffectRegistry,
    EffectContext,
    EffectResult,
)
from app.game.elements import (
    ElementMatrix,
    calculate_element_bonus,
    calculate_damage,
    get_element_matrix,
)
from app.game.validators import (
    RuleValidator,
    ValidationError,
    ValidationResult,
)
from app.game.event_generator import (
    ActionToEventGenerator,
)
from app.game.event_loop import (
    EventLoop,
    EventLoopResult,
)
from app.game.reducer import (
    apply_event,
    apply_events,
)
from app.game.engine import (
    GameEngine,
    ActionResult,
    get_engine,
)
from app.game.websocket import (
    GameManager,
    GameRoom,
    PlayerConnection,
    game_websocket_handler,
)

__all__ = [
    # Enums
    "Zone",
    "TurnPhase",
    "DamageType",
    "GameStatus",
    "CardStatus",
    "EffectTiming",
    # Actions
    "Action",
    "DrawAction",
    "PlayCardAction",
    "PromoteAction",
    "SwapAction",
    "AssociationAction",
    "EvolutionAction",
    "AttackAction",
    "PassPhaseAction",
    "ForceDefendAction",
    "ConcedeAction",
    "MultiPlayCardAction",
    "MultiSwapAction",
    "create_action",
    # Events
    "GameEvent",
    "CardDrawnEvent",
    "CardMovedEvent",
    "CardPlayedEvent",
    "CardPromotedEvent",
    "CardSwappedEvent",
    "CardAssociatedEvent",
    "CardEvolvedEvent",
    "AttackDeclaredEvent",
    "DamageDealtEvent",
    "CardDestroyedEvent",
    "ElementsConsumedEvent",
    "ElementsRestoredEvent",
    "TurnStartedEvent",
    "TurnEndedEvent",
    "PhaseChangedEvent",
    "GameStartedEvent",
    "GameEndedEvent",
    "NoDefenderEvent",
    "EffectTriggeredEvent",
    "EffectAppliedEvent",
    # Effects
    "Effect",
    "EffectTrigger",
    "EffectRegistry",
    "EffectContext",
    "EffectResult",
    # Elements
    "ElementMatrix",
    "calculate_element_bonus",
    "calculate_damage",
    "get_element_matrix",
    # Validators
    "RuleValidator",
    "ValidationError",
    "ValidationResult",
    # Event Generator
    "ActionToEventGenerator",
    # Event Loop
    "EventLoop",
    "EventLoopResult",
    # Reducer
    "apply_event",
    "apply_events",
    # Engine
    "GameEngine",
    "ActionResult",
    "get_engine",
    # WebSocket
    "GameManager",
    "GameRoom",
    "PlayerConnection",
    "game_websocket_handler",
]
