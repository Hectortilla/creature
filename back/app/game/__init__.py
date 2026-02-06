"""
Creature Card Game Engine

Event-driven game engine with a unidirectional data flow pipeline.

Pipeline Architecture:
┌─────────┐    ┌───────────┐    ┌────────────────┐    ┌───────────┐    ┌─────────┐    ┌───────────┐
│ Action  │ -> │ Validator │ -> │ EventGenerator │ -> │ EventLoop │ -> │ Reducer │ -> │ New State │
└─────────┘    └───────────┘    └────────────────┘    └───────────┘    └─────────┘    └───────────┘
     │              │                   │                   │               │
     │              │                   │                   │               └── Pure state mutations
     │              │                   │                   └── Processes events, triggers effects
     │              │                   └── Transforms action into events with computed data
     │              └── Validates rules for current game state (returns error or continues)
     └── Player intent (play card, attack, etc.) - no game logic

Module Responsibilities:
- actions.py        : Player action definitions (intent only, no computation)
- validators.py     : Rule validation against current state
- event_generator.py: Transforms validated actions into events with computed data
- event_loop.py     : Processes events sequentially, triggers card effects
- reducer.py        : Pure functions that apply events to state (only place state mutates)
- effects.py        : Card effect/skill system triggered by events
- elements.py       : Element interaction matrix and damage calculations
- engine.py         : Orchestrates the full pipeline (stateless coordinator)

Game state models are in app.models.game:
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
    state = engine.create_game(room)
    result = engine.start_game(state)
    state = result.state
    
    # Process player action
    action = PlayCardAction(player_id="...", card_uid="...", target_zone=Zone.ATTACK)
    result = engine.process_action(state, action)
    
    # Serialize using Pydantic's model_dump()
    state_dict = state.model_dump(mode='json')
"""

from app.models.game.enums import (
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
from app.models.game.events import (
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
from app.game.effects import *
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
