"""
WebSocket Game System

Modular WebSocket-based game communication system for real-time gameplay.

Architecture (dependencies point downward):
    routes/         - FastAPI WebSocket and HTTP endpoints
    session         - One connection's lifecycle (connect, join, pump, cleanup)
    message_router  - Inbound message validation and dispatch
    game_runner     - Runs the engine (start game, process actions, query state)
    lobby           - Room lifecycle (create, join, leave, list)
    room_registry   - Room membership + fan-out (Redis-backed source of truth)
    connections     - WebSocket connections and pub/sub delivery
    serialization   - Event/data serialization helpers
"""
