"""
Game Actions

Defines all player actions that can be taken during a game.
Each action represents a discrete player decision.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional
from abc import ABC, abstractmethod

from app.game.enums import TurnPhase

if TYPE_CHECKING:
    from app.game.models import GameState


@dataclass
class Action(ABC):
    """
    Base class for all game actions.
    
    Attributes:
        player_id: ID of the player performing the action
    """
    player_id: str
    
    @property
    @abstractmethod
    def valid_phases(self) -> list[TurnPhase] | None:
        """
        Return list of phases this action is valid in.
        Return None if valid in any phase.
        """
        pass
    
    @property
    @abstractmethod
    def action_type(self) -> str:
        """Return the type name of this action."""
        pass
    
    def get_description(self, state: "GameState") -> str:
        """
        Get a human-readable description of this action.
        
        Args:
            state: Game state for resolving card names, etc.
        
        Returns:
            Description string
        """
        return f"{self.action_type} action"
    
    def to_dict(self, state: "GameState") -> dict:
        """
        Convert action to a dictionary for API responses.
        
        Args:
            state: Game state for resolving card names, etc.
        
        Returns:
            Dictionary with action type, parameters, and description
        """
        return {
            "action": self.action_type,
            "description": self.get_description(state),
        }


@dataclass
class DrawAction(Action):
    """
    Action to draw cards from deck to hand.
    
    This is typically handled automatically at the start of the turn,
    but can be triggered by effects.
    
    Attributes:
        count: Number of cards to draw (default 1)
    """
    count: int = 1
    
    @property
    def valid_phases(self) -> list[TurnPhase] | None:
        return [TurnPhase.DRAW]
    
    @property
    def action_type(self) -> str:
        return "draw"
    
    def get_description(self, state: "GameState") -> str:
        return f"Draw {self.count} card{'s' if self.count != 1 else ''}"
    
    def to_dict(self, state: "GameState") -> dict:
        d = super().to_dict(state)
        d["count"] = self.count
        return d


@dataclass
class PlayCardAction(Action):
    """
    Action to play a card from hand to supporting zone.
    
    Attributes:
        card_id: Instance ID of the card to play
    """
    card_id: str
    
    @property
    def valid_phases(self) -> list[TurnPhase] | None:
        return [TurnPhase.PLACEMENT]
    
    @property
    def action_type(self) -> str:
        return "play_card"
    
    def get_description(self, state: "GameState") -> str:
        card = state.get_card(self.card_id)
        card_name = card.name if card else self.card_id
        return f"Play {card_name} to supporting zone"
    
    def to_dict(self, state: "GameState") -> dict:
        d = super().to_dict(state)
        card = state.get_card(self.card_id)
        d["card_id"] = self.card_id
        d["card_name"] = card.name if card else None
        return d


@dataclass
class PromoteAction(Action):
    """
    Action to promote a card from supporting zone to attacking zone.
    
    The card must have spent at least one full turn in the supporting zone.
    
    Attributes:
        card_id: Instance ID of the card to promote
    """
    card_id: str
    
    @property
    def valid_phases(self) -> list[TurnPhase] | None:
        return [TurnPhase.PROMOTION]
    
    @property
    def action_type(self) -> str:
        return "promote"
    
    def get_description(self, state: "GameState") -> str:
        card = state.get_card(self.card_id)
        card_name = card.name if card else self.card_id
        return f"Promote {card_name} to attacking zone"
    
    def to_dict(self, state: "GameState") -> dict:
        d = super().to_dict(state)
        card = state.get_card(self.card_id)
        d["card_id"] = self.card_id
        d["card_name"] = card.name if card else None
        return d


@dataclass
class SwapAction(Action):
    """
    Action to swap a supporting card with an attacking card.
    
    During the turn of the swap:
    - Neither card contributes elements
    - Both cards' skills remain active
    - The attacking card may still attack
    
    Attributes:
        supporting_card_id: Instance ID of the card in supporting zone
        attacking_card_id: Instance ID of the card in attacking zone
    """
    supporting_card_id: str
    attacking_card_id: str
    
    @property
    def valid_phases(self) -> list[TurnPhase] | None:
        return [TurnPhase.SWAP]
    
    @property
    def action_type(self) -> str:
        return "swap"
    
    def get_description(self, state: "GameState") -> str:
        supp = state.get_card(self.supporting_card_id)
        atk = state.get_card(self.attacking_card_id)
        supp_name = supp.name if supp else self.supporting_card_id
        atk_name = atk.name if atk else self.attacking_card_id
        return f"Swap {supp_name} with {atk_name}"
    
    def to_dict(self, state: "GameState") -> dict:
        d = super().to_dict(state)
        supp = state.get_card(self.supporting_card_id)
        atk = state.get_card(self.attacking_card_id)
        d["supporting_card_id"] = self.supporting_card_id
        d["attacking_card_id"] = self.attacking_card_id
        d["supporting_card_name"] = supp.name if supp else None
        d["attacking_card_name"] = atk.name if atk else None
        return d


@dataclass
class AssociationAction(Action):
    """
    Action to associate a card with an active creature.
    
    The association card can come from hand or supporting zone.
    Once associated:
    - Does not contribute elements
    - Cannot attack
    - Does not occupy an active zone slot
    - Cannot evolve
    - Skills are not activated
    - Cannot be de-associated
    
    Attributes:
        association_card_id: Instance ID of the card to use as association
        target_card_id: Instance ID of the card to associate with
    """
    association_card_id: str
    target_card_id: str
    
    @property
    def valid_phases(self) -> list[TurnPhase] | None:
        return [TurnPhase.ASSOCIATION]
    
    @property
    def action_type(self) -> str:
        return "associate"
    
    def get_description(self, state: "GameState") -> str:
        assoc = state.get_card(self.association_card_id)
        target = state.get_card(self.target_card_id)
        assoc_name = assoc.name if assoc else self.association_card_id
        target_name = target.name if target else self.target_card_id
        return f"Associate {assoc_name} with {target_name}"
    
    def to_dict(self, state: "GameState") -> dict:
        d = super().to_dict(state)
        assoc = state.get_card(self.association_card_id)
        target = state.get_card(self.target_card_id)
        d["association_card_id"] = self.association_card_id
        d["target_card_id"] = self.target_card_id
        d["association_card_name"] = assoc.name if assoc else None
        d["target_card_name"] = target.name if target else None
        return d


@dataclass
class EvolutionAction(Action):
    """
    Action to evolve a creature with an evolution card.
    
    Requirements:
    - Evolution card must be in hand
    - Target must be in an active zone
    - Target must have been active for at least 1 full turn
    - Target must match the evolution's required base creature
    - Cannot evolve on first or second turn
    
    Attributes:
        evolution_card_id: Instance ID of the evolution card (from hand)
        target_card_id: Instance ID of the card to evolve
    """
    evolution_card_id: str
    target_card_id: str
    
    @property
    def valid_phases(self) -> list[TurnPhase] | None:
        return [TurnPhase.EVOLUTION]
    
    @property
    def action_type(self) -> str:
        return "evolve"
    
    def get_description(self, state: "GameState") -> str:
        evo = state.get_card(self.evolution_card_id)
        target = state.get_card(self.target_card_id)
        evo_name = evo.name if evo else self.evolution_card_id
        target_name = target.name if target else self.target_card_id
        return f"Evolve {target_name} into {evo_name}"
    
    def to_dict(self, state: "GameState") -> dict:
        d = super().to_dict(state)
        evo = state.get_card(self.evolution_card_id)
        target = state.get_card(self.target_card_id)
        d["evolution_card_id"] = self.evolution_card_id
        d["target_card_id"] = self.target_card_id
        d["evolution_card_name"] = evo.name if evo else None
        d["target_card_name"] = target.name if target else None
        return d


@dataclass
class AttackAction(Action):
    """
    Action to attack with a creature.
    
    Each attacking creature may perform one attack per turn.
    Attacks consume elements and target opposing attacking creatures.
    
    Attributes:
        attacker_id: Instance ID of the attacking card
        attack_id: ID of the attack to use
        target_id: Instance ID of the target card (empty string if no defenders)
    """
    attacker_id: str
    attack_id: int
    target_id: str
    
    @property
    def valid_phases(self) -> list[TurnPhase] | None:
        return [TurnPhase.ATTACK]
    
    @property
    def action_type(self) -> str:
        return "attack"
    
    def get_description(self, state: "GameState") -> str:
        attacker = state.get_card(self.attacker_id)
        attacker_name = attacker.name if attacker else self.attacker_id
        
        # Get attack name
        attack_name = str(self.attack_id)
        if attacker:
            for atk in attacker.attacks:
                if atk.attack_id == self.attack_id:
                    attack_name = atk.name
                    break
        
        if self.target_id:
            target = state.get_card(self.target_id)
            target_name = target.name if target else self.target_id
            return f"{attacker_name} uses {attack_name} on {target_name}"
        else:
            return f"{attacker_name} uses {attack_name} (no defenders)"
    
    def to_dict(self, state: "GameState") -> dict:
        d = super().to_dict(state)
        attacker = state.get_card(self.attacker_id)
        target = state.get_card(self.target_id) if self.target_id else None
        
        attack_name = None
        if attacker:
            for atk in attacker.attacks:
                if atk.attack_id == self.attack_id:
                    attack_name = atk.name
                    break
        
        d["attacker_id"] = self.attacker_id
        d["attack_id"] = self.attack_id
        d["target_id"] = self.target_id if self.target_id else None
        d["attacker_name"] = attacker.name if attacker else None
        d["attack_name"] = attack_name
        d["target_name"] = target.name if target else None
        return d


@dataclass
class PassPhaseAction(Action):
    """
    Action to pass/end the current phase without taking any more actions.
    
    This advances the game to the next phase.
    """
    
    @property
    def valid_phases(self) -> list[TurnPhase] | None:
        # Can pass any phase
        return None
    
    @property
    def action_type(self) -> str:
        return "pass"
    
    def get_description(self, state: "GameState") -> str:
        return "Pass current phase"


@dataclass
class ForceDefendAction(Action):
    """
    Action taken when a player must move a supporting creature to defend.
    
    This is required when:
    - The opponent attacks
    - The defending player has no attacking creatures
    - The defending player has supporting creatures
    
    Attributes:
        card_id: Instance ID of the supporting card to move to attack zone
    """
    card_id: str
    
    @property
    def valid_phases(self) -> list[TurnPhase] | None:
        # This is a special action that can happen during attack phase
        return [TurnPhase.ATTACK]
    
    @property
    def action_type(self) -> str:
        return "force_defend"
    
    def get_description(self, state: "GameState") -> str:
        card = state.get_card(self.card_id)
        card_name = card.name if card else self.card_id
        return f"Move {card_name} to defend"
    
    def to_dict(self, state: "GameState") -> dict:
        d = super().to_dict(state)
        card = state.get_card(self.card_id)
        d["card_id"] = self.card_id
        d["card_name"] = card.name if card else None
        return d


@dataclass
class ConcedeAction(Action):
    """
    Action to concede the game.
    
    The player who concedes loses immediately.
    """
    
    @property
    def valid_phases(self) -> list[TurnPhase] | None:
        # Can concede at any time
        return None
    
    @property
    def action_type(self) -> str:
        return "concede"
    
    def get_description(self, state: "GameState") -> str:
        return "Concede the game"


@dataclass
class MultiPlayCardAction(Action):
    """
    Action to play multiple cards from hand to supporting zone at once.
    
    This is a convenience action for the placement phase.
    
    Attributes:
        card_ids: List of instance IDs of cards to play
    """
    card_ids: list[str] = field(default_factory=list)
    
    @property
    def valid_phases(self) -> list[TurnPhase] | None:
        return [TurnPhase.PLACEMENT]
    
    @property
    def action_type(self) -> str:
        return "multi_play_card"
    
    def get_description(self, state: "GameState") -> str:
        card_names = []
        for card_id in self.card_ids:
            card = state.get_card(card_id)
            card_names.append(card.name if card else card_id)
        return f"Play {', '.join(card_names)} to supporting zone"
    
    def to_dict(self, state: "GameState") -> dict:
        d = super().to_dict(state)
        cards_info = []
        for card_id in self.card_ids:
            card = state.get_card(card_id)
            cards_info.append({
                "card_id": card_id,
                "card_name": card.name if card else None,
            })
        d["cards"] = cards_info
        return d


@dataclass
class MultiSwapAction(Action):
    """
    Action to perform multiple swaps at once.
    
    Attributes:
        swaps: List of (supporting_card_id, attacking_card_id) tuples
    """
    swaps: list[tuple[str, str]] = field(default_factory=list)
    
    @property
    def valid_phases(self) -> list[TurnPhase] | None:
        return [TurnPhase.SWAP]
    
    @property
    def action_type(self) -> str:
        return "multi_swap"
    
    def get_description(self, state: "GameState") -> str:
        swap_descs = []
        for supp_id, atk_id in self.swaps:
            supp = state.get_card(supp_id)
            atk = state.get_card(atk_id)
            supp_name = supp.name if supp else supp_id
            atk_name = atk.name if atk else atk_id
            swap_descs.append(f"{supp_name} ↔ {atk_name}")
        return f"Swap: {', '.join(swap_descs)}"
    
    def to_dict(self, state: "GameState") -> dict:
        d = super().to_dict(state)
        swaps_info = []
        for supp_id, atk_id in self.swaps:
            supp = state.get_card(supp_id)
            atk = state.get_card(atk_id)
            swaps_info.append({
                "supporting_card_id": supp_id,
                "attacking_card_id": atk_id,
                "supporting_card_name": supp.name if supp else None,
                "attacking_card_name": atk.name if atk else None,
            })
        d["swaps"] = swaps_info
        return d


# Action type mapping for deserialization
ACTION_TYPES = {
    "draw": DrawAction,
    "play_card": PlayCardAction,
    "promote": PromoteAction,
    "swap": SwapAction,
    "associate": AssociationAction,
    "evolve": EvolutionAction,
    "attack": AttackAction,
    "pass": PassPhaseAction,
    "force_defend": ForceDefendAction,
    "concede": ConcedeAction,
    "multi_play_card": MultiPlayCardAction,
    "multi_swap": MultiSwapAction,
}


def create_action(action_type: str, player_id: str, **kwargs) -> Action:
    """
    Factory function to create an action from type name and parameters.
    
    Args:
        action_type: The type of action to create
        player_id: ID of the player performing the action
        **kwargs: Additional arguments for the specific action type
    
    Returns:
        The created action
    
    Raises:
        ValueError: If the action type is unknown
    """
    if action_type not in ACTION_TYPES:
        raise ValueError(f"Unknown action type: {action_type}")
    
    action_class = ACTION_TYPES[action_type]
    return action_class(player_id=player_id, **kwargs)

