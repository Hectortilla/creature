"""
Game State Models

Core data structures for representing game state, including cards,
players, zones, and the overall game state.

All models use Pydantic BaseModel for validation and serialization.
Uses @computed_field for derived properties to include in serialization.

Inherits shared field definitions from app.models.core for DRY with base models.
"""

# Enums
# Attack
from app.models.game.attack import (
    AttackDefinition,
    AttackResult,
)

# Base
from app.models.game.base import GameBaseModel

# Card
from app.models.game.card import GameCard, GameCardInput

# Element
from app.models.game.element import (
    ElementContribution,
    ElementPool,
)
from app.models.game.enums import (
    CardStatus,
    DamageType,
    GameStatus,
    TurnPhase,
    Zone,
)

# Events
from app.models.game.events import *

# Player
from app.models.game.player import PlayerState

# State
from app.models.game.state import (
    GameConfiguration,
    GameState,
)

# Zone
from app.models.game.zone import ZoneState
