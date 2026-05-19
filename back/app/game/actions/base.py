from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.models.game.enums import TurnPhase
from app.models.game.base import GameBaseModel
from app.models.game.events import GameEvent

if TYPE_CHECKING:
    from app.models.game.state import GameState
    from app.game.validators import ValidationResult


class Action(GameBaseModel):
    """Base class for all game actions."""
    player_id: str
    action_type: str = ""
    valid_phases: list[TurnPhase] | None = None

    def validate(self, state: "GameState") -> "ValidationResult":
        from app.game.validators import ValidationResult
        return ValidationResult(valid=True)

    def to_events(self, state: "GameState") -> list[GameEvent]:
        return []

    @classmethod
    def get_valid(cls, state: "GameState", player_id: str) -> list["Action"]:
        return []

    def to_dict(self, state: "GameState" = None) -> dict[str, Any]:
        d = self.model_dump(mode='json')
        d["action"] = self.action_type
        d["action_type"] = self.action_type
        if state:
            _enrich_card_names(d, state)
        return d


# ── Card-name enrichment for API responses ──────────────────────────────

_CARD_ID_TO_NAME = {
    "instance_id": "card_name", "attacker_id": "attacker_name",
    "target_card_id": "target_name", "supporting_card_id": "supporting_card_name",
    "attacking_card_id": "attacking_card_name", "association_card_id": "association_card_name",
    "evolution_card_id": "evolution_card_name",
}


def _enrich_card_names(d: dict, state: "GameState") -> None:
    for id_field, name_field in _CARD_ID_TO_NAME.items():
        card_id = d.get(id_field)
        if card_id:
            card = state.get_card(card_id)
            d[name_field] = card.name if card else None
    if "attacker_id" in d and "attack_id" in d:
        attacker = state.get_card(d["attacker_id"])
        if attacker:
            for atk in attacker.attacks:
                if atk.attack_id == d["attack_id"]:
                    d["attack_name"] = atk.name
                    break
