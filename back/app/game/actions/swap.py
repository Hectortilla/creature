from __future__ import annotations

from typing import TYPE_CHECKING

from app.game.actions.base import Action
from app.models.game.enums import TurnPhase, Zone
from app.models.game.events import CardSwappedEvent, GameEvent

if TYPE_CHECKING:
    from app.game.validators import ValidationResult
    from app.models.game.state import GameState


def _validate_swap_pair(
    state: GameState, supporting_zone, attacking_zone, supp_id: str, atk_id: str
) -> ValidationResult:
    from app.game.validators import ValidationResult

    if supp_id not in supporting_zone.card_ids:
        return ValidationResult(
            valid=False, error=f"Card {supp_id} is not in supporting zone", error_code="CARD_NOT_IN_SUPPORTING"
        )
    if atk_id not in attacking_zone.card_ids:
        return ValidationResult(
            valid=False, error=f"Card {atk_id} is not in attacking zone", error_code="CARD_NOT_IN_ATTACKING"
        )
    supporting_card = state.get_card(supp_id)
    if not supporting_card or not supporting_card.can_promote:
        return ValidationResult(
            valid=False,
            error=f"Card {supp_id} must spend at least one full turn in supporting zone before swapping",
            error_code="CARD_NOT_READY",
        )
    return ValidationResult(valid=True)


class SwapAction(Action):
    action_type: str = "swap"
    valid_phases: list[TurnPhase] | None = [TurnPhase.SWAP]
    supporting_card_id: str = ""
    attacking_card_id: str = ""

    def validate(self, state: GameState) -> ValidationResult:
        player = state.room.get_player(self.player_id)
        return _validate_swap_pair(
            state,
            player.zones[Zone.SUPPORTING.name],
            player.zones[Zone.ATTACKING.name],
            self.supporting_card_id,
            self.attacking_card_id,
        )

    def to_events(self, state: GameState) -> list[GameEvent]:
        return [
            CardSwappedEvent(
                game_id=state.game_id,
                player_id=self.player_id,
                supporting_card_id=self.supporting_card_id,
                attacking_card_id=self.attacking_card_id,
            )
        ]

    @classmethod
    def get_valid(cls, state: GameState, player_id: str) -> list[Action]:
        player = state.room.players[player_id]
        supp_ids = player.zones[Zone.SUPPORTING.name].card_ids
        atk_ids = player.zones[Zone.ATTACKING.name].card_ids
        return [
            cls(player_id=player_id, supporting_card_id=s, attacking_card_id=a)
            for s in supp_ids
            for a in atk_ids
            if (c := state.get_card(s)) and c.can_promote
        ]


class MultiSwapAction(Action):
    action_type: str = "multi_swap"
    valid_phases: list[TurnPhase] | None = [TurnPhase.SWAP]
    swaps: list[tuple[str, str]] = []

    def validate(self, state: GameState) -> ValidationResult:
        from app.game.validators import ValidationResult

        player = state.room.get_player(self.player_id)
        supporting_zone = player.zones[Zone.SUPPORTING.name]
        attacking_zone = player.zones[Zone.ATTACKING.name]
        used_s, used_a = set(), set()
        for s_id, a_id in self.swaps:
            if s_id in used_s:
                return ValidationResult(
                    valid=False, error=f"Card {s_id} used in multiple swaps", error_code="DUPLICATE_SWAP"
                )
            if a_id in used_a:
                return ValidationResult(
                    valid=False, error=f"Card {a_id} used in multiple swaps", error_code="DUPLICATE_SWAP"
                )
            used_s.add(s_id)
            used_a.add(a_id)
            result = _validate_swap_pair(state, supporting_zone, attacking_zone, s_id, a_id)
            if not result.valid:
                return result
        return ValidationResult(valid=True)

    def to_events(self, state: GameState) -> list[GameEvent]:
        return [
            CardSwappedEvent(game_id=state.game_id, player_id=self.player_id, supporting_card_id=s, attacking_card_id=a)
            for s, a in self.swaps
        ]
