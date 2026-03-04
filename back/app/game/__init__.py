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
