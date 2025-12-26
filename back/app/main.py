import asyncio
from contextlib import asynccontextmanager

from broadcaster import Broadcast
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import create_db_and_tables
from app.routers import (
    elements_router,
    types_router,
    characters_router,
    attacks_router,
    abilities_router,
    associations_router,
    cards_router,
)
from app.game.router import game_router

# Import models to ensure they're registered with SQLModel
from app.models.db import (
    Element, Type, Character, Attack, Ability, Association, Card
)

settings = get_settings()
broadcast = Broadcast(settings.broadcast_url)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup and connect broadcaster."""
    # create_db_and_tables()
    await broadcast.connect()
    yield
    await broadcast.disconnect()


app = FastAPI(
    title="Creature Card Game API",
    description="API for managing creature cards, attacks, abilities, and more",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(elements_router)
app.include_router(types_router)
app.include_router(characters_router)
app.include_router(attacks_router)
app.include_router(abilities_router)
app.include_router(associations_router)
app.include_router(cards_router)
app.include_router(game_router)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Creature Card Game API", "status": "healthy"}


GAME_CHANNEL = "game"


@app.websocket("/game/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    """WebSocket endpoint for real-time game communication."""
    await websocket.accept()
    
    async def receiver():
        """Receive messages from WebSocket and publish to broadcast channel."""
        async for message in websocket.iter_text():
            await websocket.send_text(f"You wrote: {message}")
            await broadcast.publish(channel=GAME_CHANNEL, message=f"Client #{client_id} says: {message}")
    
    async def sender():
        """Subscribe to broadcast channel and send messages to WebSocket."""
        async with broadcast.subscribe(channel=GAME_CHANNEL) as subscriber:
            async for event in subscriber:
                await websocket.send_text(event.message)
    
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(receiver())
            tg.create_task(sender())
    except* WebSocketDisconnect:
        await broadcast.publish(channel=GAME_CHANNEL, message=f"Client #{client_id} left the chat")
