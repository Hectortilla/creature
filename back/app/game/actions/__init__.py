"""
Game Actions Package

Re-exports all action classes so callers use:
    from app.game.actions import PlayCardAction, create_action, ACTION_TYPES
"""

from app.game.actions.association import AssociationAction
from app.game.actions.base import Action
from app.game.actions.combat import (
    AttackAction,
    ForceDefendAction,
    ResolveForcedSwapAction,
    ReviveFromGraveyardAction,
    build_combat_events,
)
from app.game.actions.evolution import EvolutionAction
from app.game.actions.placement import PlayCardAction
from app.game.actions.promotion import PromoteAction
from app.game.actions.swap import MultiSwapAction, SwapAction
from app.game.actions.turn import ConcedeAction, DrawAction, PassPhaseAction

ACTION_TYPES: dict[str, type[Action]] = {
    "draw": DrawAction,
    "play_card": PlayCardAction,
    "promote": PromoteAction,
    "swap": SwapAction,
    "associate": AssociationAction,
    "evolve": EvolutionAction,
    "attack": AttackAction,
    "pass": PassPhaseAction,
    "force_defend": ForceDefendAction,
    "resolve_forced_swap": ResolveForcedSwapAction,
    "revive_from_graveyard": ReviveFromGraveyardAction,
    "concede": ConcedeAction,
    "multi_swap": MultiSwapAction,
}


def create_action(action_type: str, player_id: str, **kwargs) -> Action:
    if action_type not in ACTION_TYPES:
        raise ValueError(f"Unknown action type: {action_type}")
    return ACTION_TYPES[action_type](player_id=player_id, **kwargs)
