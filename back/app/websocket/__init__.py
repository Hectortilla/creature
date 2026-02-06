"""
WebSocket Game System

Modular WebSocket-based game communication system for real-time gameplay.

Architecture:
    routes/         - FastAPI WebSocket and HTTP endpoints
    message_handler - Incoming message routing and validation
    room_manager    - Room lifecycle (create, join, leave, start game, process actions)
    connection      - WebSocket connection management with Redis pub/sub
    models          - Data models (GameRoom, etc.)
    serialization   - Event/data serialization helpers
"""
