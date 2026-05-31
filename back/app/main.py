"""
Creature Card Game API

Main FastAPI application entrypoint.
"""

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import models to ensure they're registered with SQLModel
from app.routers import (
    abilities_router,
    associations_router,
    attacks_router,
    auth_router,
    cards_router,
    characters_router,
    decks_router,
    elements_router,
    types_router,
)
from app.settings.config import get_settings
from app.settings.lifespan import lifespan
from app.settings.logging import configure_logging
from app.settings.observability import setup_observability
from app.websocket.routes import router as websocket_router

from .settings.admin.index import setup_admin

settings = get_settings()
configure_logging(level=settings.log_level, json_logs=settings.log_json)

app = FastAPI(
    title="Creature Card Game API",
    description="API for managing creature cards, attacks, abilities, and real-time game play",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(CorrelationIdMiddleware)

# Setup admin panel
setup_admin(app)

# Include routers
app.include_router(auth_router)
app.include_router(elements_router)
app.include_router(types_router)
app.include_router(characters_router)
app.include_router(attacks_router)
app.include_router(abilities_router)
app.include_router(associations_router)
app.include_router(cards_router)
app.include_router(decks_router)
app.include_router(websocket_router, prefix="/game", tags=["Game"])

# Metrics (/metrics) and optional OpenTelemetry tracing.
setup_observability(app, settings)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Creature Card Game API", "status": "healthy"}
