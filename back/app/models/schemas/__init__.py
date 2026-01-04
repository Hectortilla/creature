from app.models.schemas.element import ElementCreate, ElementRead
from app.models.schemas.type import TypeCreate, TypeRead
from app.models.schemas.character import CharacterCreate, CharacterRead
from app.models.schemas.ability import AbilityCreate, AbilityRead
from app.models.schemas.association import AssociationCreate, AssociationRead
from app.models.schemas.attack import AttackCreate, AttackRead, AttackReadWithElement
from app.models.schemas.card import CardCreate, CardRead, CardReadWithRelations
from app.models.schemas.user import UserCreate, UserRead, Token, TokenData
from app.models.schemas.deck import DeckCreate, DeckUpdate, DeckRead, DeckReadWithCards, DeckReadSummary
# WebSocket schemas are available via app.models.schemas.websocket.client and app.models.schemas.websocket.server

