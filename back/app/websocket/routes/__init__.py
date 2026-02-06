"""
WebSocket Routes Module

Combines game and type generation routers.
"""

from fastapi import APIRouter

from app.websocket.routes.game import router as game_router
from app.websocket.routes.types import router as types_router

router = APIRouter()
router.include_router(game_router)
router.include_router(types_router)
