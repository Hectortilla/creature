from __future__ import annotations

from typing import TYPE_CHECKING

from app.game.actions.base import Action
from app.models.game.enums import TurnPhase, Zone
from app.models.game.events import CardPromotedEvent, GameEvent

if TYPE_CHECKING:
    from app.game.validators import ValidationResult
    from app.models.game.state import GameState


class PromoteAction(Action):
    action_type: str = "promote"
    valid_phases: list[TurnPhase] | None = [TurnPhase.PROMOTION]
    instance_id: str = ""

    def validate(self, state: GameState) -> ValidationResult:
        from app.game.validators import ValidationResult

        player = state.room.get_player(self.player_id)
        if self.instance_id not in player.zones[Zone.SUPPORTING.name].card_ids:
            return ValidationResult(
                valid=False, error="Card is not in supporting zone", error_code="CARD_NOT_IN_SUPPORTING"
            )
        if player.zones[Zone.ATTACKING.name].is_full:
            return ValidationResult(
                valid=False, error="Attacking zone is full (max 2 cards)", error_code="ATTACKING_ZONE_FULL"
            )
        card = state.get_card(self.instance_id)
        if not card or not card.can_promote:
            return ValidationResult(
                valid=False,
                error="Card must spend at least one full turn in supporting zone before promotion",
                error_code="CARD_NOT_READY",
            )
        return ValidationResult(valid=True)

    def to_events(self, state: GameState) -> list[GameEvent]:
        card = state.get_card(self.instance_id)
        if not card:
            return []
        return [
            CardPromotedEvent(
                game_id=state.game_id,
                player_id=self.player_id,
                instance_id=self.instance_id,
                card_id=card.card_id,
                card_name=card.name,
            )
        ]

    @classmethod
    def get_valid(cls, state: GameState, player_id: str) -> list[Action]:
        player = state.room.players[player_id]
        if player.zones[Zone.ATTACKING.name].is_full:
            return []
        return [
            cls(player_id=player_id, instance_id=cid)
            for cid in player.zones[Zone.SUPPORTING.name].card_ids
            if (card := state.get_card(cid)) is not None and card.can_promote
        ]
