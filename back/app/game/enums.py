"""
Game Enumerations

Defines all enums used throughout the game engine.
"""

from enum import Enum, auto


class Zone(Enum):
    """
    Zones in the game. Each player has their own instance of each zone.
    
    - DECK: Contains 22 cards at game start, cards are drawn from here
    - HAND: Cards held by player, can be played from here
    - SUPPORTING: Max 3 cards, cannot attack but contribute elements/skills
    - ATTACKING: Max 2 cards, can attack and contribute elements/skills
    - GRAVEYARD: Destroyed cards go here, no effect
    """
    DECK = auto()
    HAND = auto()
    SUPPORTING = auto()
    ATTACKING = auto()
    GRAVEYARD = auto()


class TurnPhase(Enum):
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
    DRAW = auto()
    PLACEMENT = auto()
    PROMOTION = auto()
    SWAP = auto()
    ASSOCIATION = auto()
    EVOLUTION = auto()
    ATTACK = auto()
    
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


class DamageType(Enum):
    """
    Types of damage in the game.
    
    - PHYSICAL: Reduced by physical defense
    - MAGICAL: Reduced by magical defense
    """
    PHYSICAL = auto()
    MAGICAL = auto()


class GameStatus(Enum):
    """
    Overall game status.
    
    - WAITING: Game created, waiting for players
    - STARTING: Game is initializing
    - IN_PROGRESS: Game is actively being played
    - PAUSED: Game is paused (e.g., waiting for forced defend)
    - FINISHED: Game has ended
    """
    WAITING = auto()
    STARTING = auto()
    IN_PROGRESS = auto()
    PAUSED = auto()
    FINISHED = auto()


class CardStatus(Enum):
    """
    Status flags for cards in active zones.
    
    - READY: Card is ready and contributing normally
    - SWAPPED: Card was swapped this turn, no element contribution
    - EXHAUSTED: Card has attacked this turn
    - ASSOCIATED: Card is being used as an association
    """
    READY = auto()
    SWAPPED = auto()
    EXHAUSTED = auto()
    ASSOCIATED = auto()


class EffectTiming(Enum):
    """
    When effects trigger.
    
    - IMMEDIATE: Triggers immediately when condition is met
    - START_OF_TURN: Triggers at the start of owner's turn
    - END_OF_TURN: Triggers at the end of owner's turn
    - ON_ATTACK: Triggers when this card attacks
    - ON_DEFEND: Triggers when this card is attacked
    - ON_DAMAGE: Triggers when this card takes damage
    - ON_DESTROY: Triggers when this card is destroyed
    - ON_PLAY: Triggers when this card enters play
    - ON_PROMOTE: Triggers when this card moves to attacking zone
    - PASSIVE: Always active while card is in active zone
    """
    IMMEDIATE = auto()
    START_OF_TURN = auto()
    END_OF_TURN = auto()
    ON_ATTACK = auto()
    ON_DEFEND = auto()
    ON_DAMAGE = auto()
    ON_DESTROY = auto()
    ON_PLAY = auto()
    ON_PROMOTE = auto()
    PASSIVE = auto()

