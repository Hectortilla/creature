from __future__ import annotations

from typing import TYPE_CHECKING

from app.models.game.enums import Zone, TurnPhase
from app.models.game.events import GameEvent, CardPlayedEvent
from app.game.actions.base import Action

if TYPE_CHECKING:
    from app.models.game.state import GameState
    from app.game.validators import ValidationResult


class PlayCardAction(Action):
    action_type: str = "play_card"
    valid_phases: list[TurnPhase] | None = [TurnPhase.PLACEMENT]
    instance_ids: list[str] = []

    def validate(self, state: "GameState") -> "ValidationResult":
        from app.game.validators import ValidationResult
        if not self.instance_ids:
            return ValidationResult(valid=False, error="No cards to play", error_code="NO_CARDS")
        player = state.room.get_player(self.player_id)
        supporting = player.zones[Zone.SUPPORTING.name]
        hand = player.zones[Zone.HAND.name]
        available = supporting.available_slots()
        if len(self.instance_ids) > available:
            return ValidationResult(valid=False, error=f"Not enough slots (have {available}, need {len(self.instance_ids)})", error_code="NOT_ENOUGH_SLOTS")
        if len(self.instance_ids) != len(set(self.instance_ids)):
            return ValidationResult(valid=False, error="Duplicate cards in play action", error_code="DUPLICATE_CARDS")
        for cid in self.instance_ids:
            result = self._validate_card(state, hand, cid)
            if not result.valid:
                return result
        return ValidationResult(valid=True)

    @staticmethod
    def _validate_card(state: "GameState", hand, instance_id: str) -> "ValidationResult":
        from app.game.validators import ValidationResult
        if instance_id not in hand.card_ids:
            return ValidationResult(valid=False, error=f"Card {instance_id} is not in your hand", error_code="CARD_NOT_IN_HAND")
        card = state.get_card(instance_id)
        if card and card.is_evolution:
            return ValidationResult(valid=False, error=f"Evolution card {instance_id} cannot be placed directly; use the Evolution Phase", error_code="EVOLUTION_CARD_PLACEMENT")
        return ValidationResult(valid=True)

    def to_events(self, state: "GameState") -> list[GameEvent]:
        events: list[GameEvent] = []
        for instance_id in self.instance_ids:
            card = state.get_card(instance_id)
            if card:
                events.append(CardPlayedEvent(
                    game_id=state.game_id, player_id=self.player_id,
                    instance_id=instance_id, card_id=card.card_id, card_name=card.name,
                ))
        return events

    @classmethod
    def get_valid(cls, state: "GameState", player_id: str) -> list[Action]:
        player = state.room.players[player_id]
        if player.zones[Zone.SUPPORTING.name].is_full:
            return []
        return [
            cls(player_id=player_id, instance_ids=[cid])
            for cid in player.zones[Zone.HAND.name].card_ids
            if (c := state.get_card(cid)) and not c.is_evolution
        ]
