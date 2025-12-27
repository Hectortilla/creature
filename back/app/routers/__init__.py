from app.routers.elements import router as elements_router
from app.routers.types import router as types_router
from app.routers.characters import router as characters_router
from app.routers.attacks import router as attacks_router
from app.routers.abilities import router as abilities_router
from app.routers.associations import router as associations_router
from app.routers.cards import router as cards_router
from app.routers.auth import router as auth_router
from app.routers.decks import router as decks_router

__all__ = [
    "elements_router",
    "types_router",
    "characters_router",
    "attacks_router",
    "abilities_router",
    "associations_router",
    "cards_router",
    "auth_router",
    "decks_router",
]

