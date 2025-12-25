"""
Creature Card Game Engine

Event-driven game engine with clean architecture:
    Action → Validator → Evaluator → Events → EventLoop → Reducer → New State

Modules:
- enums: Game enumerations (zones, phases, damage types)
- models: Game state models (cards, players, zones) 
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

Usage:
    from app.game import get_engine
    from app.game.models import GameState
    from app.game.actions import PlayCardAction
    
    engine = get_engine()
    state = engine.create_game(...)
    result = engine.start_game(state)
    state = result.state
    
    action = PlayCardAction(player_id="p1", card_id="...")
    result = engine.process_action(state, action)
    new_state = result.state
"""

from app.game.enums import (
    Zone,
    TurnPhase,
    DamageType,
    GameStatus,
    CardStatus,
    EffectTiming,
)
from app.game.models import (
    GameCard,
    PlayerState,
    ZoneState,
    GameState,
    ElementContribution,
    AttackDefinition,
    AttackResult,
    GameConfiguration,
    ElementPool,
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
    create_action,
)
from app.game.events import (
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

__all__ = [
    # Enums
    "Zone",
    "TurnPhase",
    "DamageType",
    "GameStatus",
    "CardStatus",
    "EffectTiming",
    # Models
    "GameCard",
    "PlayerState",
    "ZoneState",
    "GameState",
    "ElementContribution",
    "AttackDefinition",
    "AttackResult",
    "GameConfiguration",
    "ElementPool",
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
]
