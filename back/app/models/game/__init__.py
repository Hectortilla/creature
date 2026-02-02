"""
Game State Models

Core data structures for representing game state, including cards,
players, zones, and the overall game state.

All models use Pydantic BaseModel for validation and serialization.
Uses @computed_field for derived properties to include in serialization.

Inherits shared field definitions from app.models.core for DRY with base models.
"""

# Enums
from app.models.game.enums import (
    Zone,
    TurnPhase,
    DamageType,
    GameStatus,
    CardStatus,
    EffectTiming,
)

# Base
from app.models.game.base import GameBaseModel

# Element
from app.models.game.element import (
    ElementContribution,
    ElementPool,
)

# Attack
from app.models.game.attack import (
    AttackDefinition,
    AttackResult,
)

# Card
from app.models.game.card import GameCard, GameCardInput, GameCardInput

# Zone
from app.models.game.zone import ZoneState

# Player
from app.models.game.player import PlayerState

# State
from app.models.game.state import (
    GameConfiguration,
    GameState,
)

# Events
from app.models.game.events import *
