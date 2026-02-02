"""
Game Actions

Defines all player actions that can be taken during a game.
Each action represents a discrete player decision.

All actions use Pydantic BaseModel for validation and serialization.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Any
from abc import ABC, abstractmethod

from app.models.game.enums import TurnPhase
from app.models.game.base import GameBaseModel

if TYPE_CHECKING:
    from app.models.game.state import GameState


class Action(GameBaseModel, ABC):
    """
    Base class for all game actions.
    
    Uses Pydantic's model_dump() for serialization.
    """
    player_id: str
    
    @property
    @abstractmethod
    def valid_phases(self) -> list[TurnPhase] | None:
        """Return list of phases this action is valid in, or None for any phase."""
        pass
    
    @property
    @abstractmethod
    def action_type(self) -> str:
        """Return the type name of this action."""
        pass
    
    def get_description(self, state: "GameState" = None) -> str:
        """Get a human-readable description of this action."""
        return f"{self.action_type} action"
    
    def to_dict(self, state: "GameState" = None) -> dict[str, Any]:
        """
        Convert action to a dictionary for API responses.
        Includes action type and description.
        """
        d = self.model_dump(mode='json')
        d["action"] = self.action_type
        d["description"] = self.get_description(state)
        return d


class DrawAction(Action):
    """Action to draw cards from deck to hand."""
    count: int = 1
    
    @property
    def valid_phases(self) -> list[TurnPhase] | None:
        return [TurnPhase.DRAW]
    
    @property
    def action_type(self) -> str:
        return "draw"
    
    def get_description(self, state: "GameState" = None) -> str:
        return f"Draw {self.count} card{'s' if self.count != 1 else ''}"


class PlayCardAction(Action):
    """Action to play a card from hand to supporting zone."""
    card_id: str = ""
    
    @property
    def valid_phases(self) -> list[TurnPhase] | None:
        return [TurnPhase.PLACEMENT]
    
    @property
    def action_type(self) -> str:
        return "play_card"
    
    def get_description(self, state: "GameState" = None) -> str:
        if state:
            card = state.get_card(self.card_id)
            card_name = card.name if card else self.card_id
        else:
            card_name = self.card_id
        return f"Play {card_name} to supporting zone"
    
    def to_dict(self, state: "GameState" = None) -> dict[str, Any]:
        d = super().to_dict(state)
        if state:
            card = state.get_card(self.card_id)
            d["card_name"] = card.name if card else None
        return d


class PromoteAction(Action):
    """Action to promote a card from supporting zone to attacking zone."""
    card_id: str = ""
    
    @property
    def valid_phases(self) -> list[TurnPhase] | None:
        return [TurnPhase.PROMOTION]
    
    @property
    def action_type(self) -> str:
        return "promote"
    
    def get_description(self, state: "GameState" = None) -> str:
        if state:
            card = state.get_card(self.card_id)
            card_name = card.name if card else self.card_id
        else:
            card_name = self.card_id
        return f"Promote {card_name} to attacking zone"
    
    def to_dict(self, state: "GameState" = None) -> dict[str, Any]:
        d = super().to_dict(state)
        if state:
            card = state.get_card(self.card_id)
            d["card_name"] = card.name if card else None
        return d


class SwapAction(Action):
    """Action to swap a supporting card with an attacking card."""
    supporting_card_id: str = ""
    attacking_card_id: str = ""
    
    @property
    def valid_phases(self) -> list[TurnPhase] | None:
        return [TurnPhase.SWAP]
    
    @property
    def action_type(self) -> str:
        return "swap"
    
    def get_description(self, state: "GameState" = None) -> str:
        if state:
            supp = state.get_card(self.supporting_card_id)
            atk = state.get_card(self.attacking_card_id)
            supp_name = supp.name if supp else self.supporting_card_id
            atk_name = atk.name if atk else self.attacking_card_id
        else:
            supp_name = self.supporting_card_id
            atk_name = self.attacking_card_id
        return f"Swap {supp_name} with {atk_name}"
    
    def to_dict(self, state: "GameState" = None) -> dict[str, Any]:
        d = super().to_dict(state)
        if state:
            supp = state.get_card(self.supporting_card_id)
            atk = state.get_card(self.attacking_card_id)
            d["supporting_card_name"] = supp.name if supp else None
            d["attacking_card_name"] = atk.name if atk else None
        return d


class AssociationAction(Action):
    """Action to associate a card with an active creature."""
    association_card_id: str = ""
    target_card_id: str = ""
    
    @property
    def valid_phases(self) -> list[TurnPhase] | None:
        return [TurnPhase.ASSOCIATION]
    
    @property
    def action_type(self) -> str:
        return "associate"
    
    def get_description(self, state: "GameState" = None) -> str:
        if state:
            assoc = state.get_card(self.association_card_id)
            target = state.get_card(self.target_card_id)
            assoc_name = assoc.name if assoc else self.association_card_id
            target_name = target.name if target else self.target_card_id
        else:
            assoc_name = self.association_card_id
            target_name = self.target_card_id
        return f"Associate {assoc_name} with {target_name}"
    
    def to_dict(self, state: "GameState" = None) -> dict[str, Any]:
        d = super().to_dict(state)
        if state:
            assoc = state.get_card(self.association_card_id)
            target = state.get_card(self.target_card_id)
            d["association_card_name"] = assoc.name if assoc else None
            d["target_card_name"] = target.name if target else None
        return d


class EvolutionAction(Action):
    """Action to evolve a creature with an evolution card."""
    evolution_card_id: str = ""
    target_card_id: str = ""
    
    @property
    def valid_phases(self) -> list[TurnPhase] | None:
        return [TurnPhase.EVOLUTION]
    
    @property
    def action_type(self) -> str:
        return "evolve"
    
    def get_description(self, state: "GameState" = None) -> str:
        if state:
            evo = state.get_card(self.evolution_card_id)
            target = state.get_card(self.target_card_id)
            evo_name = evo.name if evo else self.evolution_card_id
            target_name = target.name if target else self.target_card_id
        else:
            evo_name = self.evolution_card_id
            target_name = self.target_card_id
        return f"Evolve {target_name} into {evo_name}"
    
    def to_dict(self, state: "GameState" = None) -> dict[str, Any]:
        d = super().to_dict(state)
        if state:
            evo = state.get_card(self.evolution_card_id)
            target = state.get_card(self.target_card_id)
            d["evolution_card_name"] = evo.name if evo else None
            d["target_card_name"] = target.name if target else None
        return d


class AttackAction(Action):
    """Action to attack with a creature."""
    attacker_id: str = ""
    attack_id: int = 0
    target_card_id: str = ""
    
    @property
    def valid_phases(self) -> list[TurnPhase] | None:
        return [TurnPhase.ATTACK]
    
    @property
    def action_type(self) -> str:
        return "attack"
    
    def get_description(self, state: "GameState" = None) -> str:
        if state:
            attacker = state.get_card(self.attacker_id)
            attacker_name = attacker.name if attacker else self.attacker_id
            
            attack_name = str(self.attack_id)
            if attacker:
                for atk in attacker.attacks:
                    if atk.attack_id == self.attack_id:
                        attack_name = atk.name
                        break
            
            if self.target_card_id:
                target = state.get_card(self.target_card_id)
                target_name = target.name if target else self.target_card_id
                return f"{attacker_name} uses {attack_name} on {target_name}"
            else:
                return f"{attacker_name} uses {attack_name} (no defenders)"
        else:
            return f"Attack with {self.attacker_id}"
    
    def to_dict(self, state: "GameState" = None) -> dict[str, Any]:
        d = super().to_dict(state)
        if state:
            attacker = state.get_card(self.attacker_id)
            target = state.get_card(self.target_card_id) if self.target_card_id else None
            
            attack_name = None
            if attacker:
                for atk in attacker.attacks:
                    if atk.attack_id == self.attack_id:
                        attack_name = atk.name
                        break
            
            d["attacker_name"] = attacker.name if attacker else None
            d["attack_name"] = attack_name
            d["target_name"] = target.name if target else None
        return d


class PassPhaseAction(Action):
    """Action to pass/end the current phase."""
    
    @property
    def valid_phases(self) -> list[TurnPhase] | None:
        return None
    
    @property
    def action_type(self) -> str:
        return "pass"
    
    def get_description(self, state: "GameState" = None) -> str:
        return "Pass current phase"


class ForceDefendAction(Action):
    """Action taken when a player must move a supporting creature to defend."""
    card_id: str = ""
    
    @property
    def valid_phases(self) -> list[TurnPhase] | None:
        return [TurnPhase.ATTACK]
    
    @property
    def action_type(self) -> str:
        return "force_defend"
    
    def get_description(self, state: "GameState" = None) -> str:
        if state:
            card = state.get_card(self.card_id)
            card_name = card.name if card else self.card_id
        else:
            card_name = self.card_id
        return f"Move {card_name} to defend"
    
    def to_dict(self, state: "GameState" = None) -> dict[str, Any]:
        d = super().to_dict(state)
        if state:
            card = state.get_card(self.card_id)
            d["card_name"] = card.name if card else None
        return d


class ConcedeAction(Action):
    """Action to concede the game."""
    
    @property
    def valid_phases(self) -> list[TurnPhase] | None:
        return None
    
    @property
    def action_type(self) -> str:
        return "concede"
    
    def get_description(self, state: "GameState" = None) -> str:
        return "Concede the game"


class MultiPlayCardAction(Action):
    """Action to play multiple cards from hand to supporting zone at once."""
    card_ids: list[str] = []
    
    @property
    def valid_phases(self) -> list[TurnPhase] | None:
        return [TurnPhase.PLACEMENT]
    
    @property
    def action_type(self) -> str:
        return "multi_play_card"
    
    def get_description(self, state: "GameState" = None) -> str:
        if state:
            card_names = []
            for card_id in self.card_ids:
                card = state.get_card(card_id)
                card_names.append(card.name if card else card_id)
            return f"Play {', '.join(card_names)} to supporting zone"
        else:
            return f"Play {len(self.card_ids)} cards to supporting zone"
    
    def to_dict(self, state: "GameState" = None) -> dict[str, Any]:
        d = super().to_dict(state)
        if state:
            cards_info = []
            for card_id in self.card_ids:
                card = state.get_card(card_id)
                cards_info.append({
                    "card_id": card_id,
                    "card_name": card.name if card else None,
                })
            d["cards"] = cards_info
        return d


class MultiSwapAction(Action):
    """Action to perform multiple swaps at once."""
    swaps: list[tuple[str, str]] = []
    
    @property
    def valid_phases(self) -> list[TurnPhase] | None:
        return [TurnPhase.SWAP]
    
    @property
    def action_type(self) -> str:
        return "multi_swap"
    
    def get_description(self, state: "GameState" = None) -> str:
        if state:
            swap_descs = []
            for supp_id, atk_id in self.swaps:
                supp = state.get_card(supp_id)
                atk = state.get_card(atk_id)
                supp_name = supp.name if supp else supp_id
                atk_name = atk.name if atk else atk_id
                swap_descs.append(f"{supp_name} ↔ {atk_name}")
            return f"Swap: {', '.join(swap_descs)}"
        else:
            return f"Perform {len(self.swaps)} swaps"
    
    def to_dict(self, state: "GameState" = None) -> dict[str, Any]:
        d = super().to_dict(state)
        if state:
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
    
    Raises:
        ValueError: If the action type is unknown
    """
    if action_type not in ACTION_TYPES:
        raise ValueError(f"Unknown action type: {action_type}")
    
    action_class = ACTION_TYPES[action_type]
    return action_class(player_id=player_id, **kwargs)
