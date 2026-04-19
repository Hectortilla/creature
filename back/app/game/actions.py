"""
Game Actions

All player actions that can be taken during a game.
Each action is a thin data container with a type tag and valid-phase metadata.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.models.game.enums import TurnPhase
from app.models.game.base import GameBaseModel

if TYPE_CHECKING:
    from app.models.game.state import GameState


# ── Base ────────────────────────────────────────────────────────────────

class Action(GameBaseModel):
    """Base class for all game actions."""
    player_id: str

    # Subclasses set these as class attributes — no @property boilerplate.
    action_type: str = ""
    valid_phases: list[TurnPhase] | None = None

    def to_dict(self, state: "GameState" = None) -> dict[str, Any]:
        d = self.model_dump(mode='json')
        d["action"] = self.action_type
        d["action_type"] = self.action_type
        # Resolve card names for display (generic — works for any card-id field)
        if state:
            _enrich_card_names(d, state)
        return d


# ── Actions ─────────────────────────────────────────────────────────────

class DrawAction(Action):
    action_type: str = "draw"
    valid_phases: list[TurnPhase] | None = [TurnPhase.DRAW]
    count: int = 1


class PlayCardAction(Action):
    action_type: str = "play_card"
    valid_phases: list[TurnPhase] | None = [TurnPhase.PLACEMENT]
    instance_id: str = ""


class MultiPlayCardAction(Action):
    action_type: str = "multi_play_card"
    valid_phases: list[TurnPhase] | None = [TurnPhase.PLACEMENT]
    instance_ids: list[str] = []


class PromoteAction(Action):
    action_type: str = "promote"
    valid_phases: list[TurnPhase] | None = [TurnPhase.PROMOTION]
    instance_id: str = ""


class SwapAction(Action):
    action_type: str = "swap"
    valid_phases: list[TurnPhase] | None = [TurnPhase.SWAP]
    supporting_card_id: str = ""
    attacking_card_id: str = ""


class MultiSwapAction(Action):
    action_type: str = "multi_swap"
    valid_phases: list[TurnPhase] | None = [TurnPhase.SWAP]
    swaps: list[tuple[str, str]] = []


class AssociationAction(Action):
    action_type: str = "associate"
    valid_phases: list[TurnPhase] | None = [TurnPhase.ASSOCIATION]
    association_card_id: str = ""
    target_card_id: str = ""


class EvolutionAction(Action):
    action_type: str = "evolve"
    valid_phases: list[TurnPhase] | None = [TurnPhase.EVOLUTION]
    evolution_card_id: str = ""
    target_card_id: str = ""


class AttackAction(Action):
    action_type: str = "attack"
    valid_phases: list[TurnPhase] | None = [TurnPhase.ATTACK]
    attacker_id: str = ""
    attack_id: int = 0
    target_card_id: str = ""


class PassPhaseAction(Action):
    action_type: str = "pass"
    valid_phases: list[TurnPhase] | None = None


class ForceDefendAction(Action):
    action_type: str = "force_defend"
    valid_phases: list[TurnPhase] | None = [TurnPhase.ATTACK]
    instance_id: str = ""


class ConcedeAction(Action):
    action_type: str = "concede"
    valid_phases: list[TurnPhase] | None = None


# ── Factory ─────────────────────────────────────────────────────────────

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
    "concede": ConcedeAction,
    "multi_play_card": MultiPlayCardAction,
    "multi_swap": MultiSwapAction,
}


def create_action(action_type: str, player_id: str, **kwargs) -> Action:
    if action_type not in ACTION_TYPES:
        raise ValueError(f"Unknown action type: {action_type}")
    return ACTION_TYPES[action_type](player_id=player_id, **kwargs)


# ── Card-name enrichment for API responses ──────────────────────────────

# Fields that contain card instance IDs → corresponding name field
_CARD_ID_TO_NAME = {
    "instance_id": "card_name",
    "attacker_id": "attacker_name",
    "target_card_id": "target_name",
    "supporting_card_id": "supporting_card_name",
    "attacking_card_id": "attacking_card_name",
    "association_card_id": "association_card_name",
    "evolution_card_id": "evolution_card_name",
}


def _enrich_card_names(d: dict, state: "GameState") -> None:
    """Add human-readable card names to an action dict."""
    for id_field, name_field in _CARD_ID_TO_NAME.items():
        card_id = d.get(id_field)
        if card_id:
            card = state.get_card(card_id)
            d[name_field] = card.name if card else None

    # Attack name resolution
    if "attacker_id" in d and "attack_id" in d:
        attacker = state.get_card(d["attacker_id"])
        if attacker:
            for atk in attacker.attacks:
                if atk.attack_id == d["attack_id"]:
                    d["attack_name"] = atk.name
                    break
