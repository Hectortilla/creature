"""
Game Enumerations

Defines all enums used in the game system.
"""

from enum import Enum


class Zone(str, Enum):
    """
    Zones in the game. Each player has their own instance of each zone.
    
    - DECK: Contains 22 cards at game start, cards are drawn from here
    - HAND: Cards held by player, can be played from here
    - SUPPORTING: Max 3 cards, cannot attack but contribute elements/effects
    - ATTACKING: Max 2 cards, can attack and contribute elements/effects
    - GRAVEYARD: Destroyed cards go here, no effect
    """
    DECK = "DECK"
    HAND = "HAND"
    SUPPORTING = "SUPPORTING"
    ATTACKING = "ATTACKING"
    GRAVEYARD = "GRAVEYARD"
    EXILED = "EXILED"


class TurnPhase(str, Enum):
    """
    Turn phases in order of execution.
    
    Each player's turn follows this sequence:
    1. DRAW - Draw cards from deck
    2. PLACEMENT - Place cards from hand to supporting zone
    3. PROMOTION - Move cards from supporting to attacking zone
    4. SWAP - Swap supporting and attacking cards
    5. ASSOCIATION - Apply association cards
    6. EVOLUTION - Evolve eligible creatures
    7. ATTACK - Perform attacks with attacking creatures
    """
    DRAW = "DRAW"
    PLACEMENT = "PLACEMENT"
    PROMOTION = "PROMOTION"
    SWAP = "SWAP"
    ASSOCIATION = "ASSOCIATION"
    EVOLUTION = "EVOLUTION"
    ATTACK = "ATTACK"
    
    @classmethod
    def get_order(cls) -> list["TurnPhase"]:
        """Get phases in execution order."""
        return [
            cls.DRAW,
            cls.PLACEMENT,
            cls.PROMOTION,
            cls.SWAP,
            cls.ASSOCIATION,
            cls.EVOLUTION,
            cls.ATTACK,
        ]
    
    def next_phase(self) -> "TurnPhase | None":
        """Get the next phase, or None if this is the last phase."""
        order = self.get_order()
        idx = order.index(self)
        if idx < len(order) - 1:
            return order[idx + 1]
        return None


class DamageType(str, Enum):
    """
    Types of damage in the game.
    
    - PHYSICAL: Reduced by physical defense
    - MAGICAL: Reduced by magical defense
    """
    PHYSICAL = "PHYSICAL"
    MAGICAL = "MAGICAL"


class GameStatus(str, Enum):
    """
    Overall game status.
    
    - WAITING: Game created, waiting for players
    - STARTING: Game is initializing
    - IN_PROGRESS: Game is actively being played
    - PAUSED: Game is paused (e.g., waiting for forced defend)
    - FINISHED: Game has ended
    """
    WAITING = "WAITING"
    STARTING = "STARTING"
    IN_PROGRESS = "IN_PROGRESS"
    PAUSED = "PAUSED"
    FINISHED = "FINISHED"


class CardStatus(str, Enum):
    """
    Status flags for cards in active zones.

    - READY: Card is ready and contributing normally
    - SWAPPED: Card was swapped this turn, no element contribution
    - ASSOCIATED: Card is being used as an association
    """
    READY = "READY"
    SWAPPED = "SWAPPED"
    ASSOCIATED = "ASSOCIATED"


class StatusType(str, Enum):
    """
    Temporary effect statuses applied by card effects.
    """
    BLOCK_ATTACK = "BLOCK_ATTACK"
    DICE_LOCKED_ATTACK = "DICE_LOCKED_ATTACK"
    DAMAGE_OVER_TIME = "DAMAGE_OVER_TIME"
    REVIVE_SWAPPABLE = "REVIVE_SWAPPABLE"


__all__ = [
    "Zone",
    "TurnPhase",
    "DamageType",
    "GameStatus",
    "CardStatus",
    "StatusType",
]
