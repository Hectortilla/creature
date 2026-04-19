"""
Creature Card Game Engine

Event-driven game engine with self-contained actions.

Pipeline:
    Action → Validator (common pre-checks) → action.to_events(state) → EventLoop → Reducer → New State

Module Responsibilities:
- actions.py    : Self-contained actions (validate, to_events, get_valid)
- combat.py     : Shared combat event generation (damage, destruction, reflection)
- validators.py : Common pre-checks (game status, active player, phase)
- event_loop.py : Processes events sequentially, triggers card effects
- reducer.py    : Pure functions that apply events to state
- effects.py    : Card effect/skill system triggered by events
- elements.py   : Element interaction matrix and damage calculations
- engine.py     : Orchestrates the full pipeline (stateless coordinator)
"""
