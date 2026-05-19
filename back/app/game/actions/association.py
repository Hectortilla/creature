from __future__ import annotations

from typing import TYPE_CHECKING

from app.models.game.enums import Zone, TurnPhase
from app.models.game.events import GameEvent, CardAssociatedEvent
from app.game.actions.base import Action

if TYPE_CHECKING:
    from app.models.game.state import GameState
    from app.game.validators import ValidationResult


class AssociationAction(Action):
    action_type: str = "associate"
    valid_phases: list[TurnPhase] | None = [TurnPhase.ASSOCIATION]
    association_card_id: str = ""
    target_card_id: str = ""

    def validate(self, state: "GameState") -> "ValidationResult":
        from app.game.validators import ValidationResult
        player = state.room.get_player(self.player_id)
        if state.is_first_turn(self.player_id):
            return ValidationResult(valid=False, error="Cannot associate cards on first turn", error_code="FIRST_TURN_RESTRICTION")
        if self.association_card_id == self.target_card_id:
            return ValidationResult(valid=False, error="Cannot associate a card with itself", error_code="SELF_ASSOCIATION")
        hand = player.zones[Zone.HAND.name]
        supporting = player.zones[Zone.SUPPORTING.name]
        if self.association_card_id not in hand.card_ids and self.association_card_id not in supporting.card_ids:
            return ValidationResult(valid=False, error="Association card must be in hand or supporting zone", error_code="INVALID_ASSOCIATION_SOURCE")
        attacking = player.zones[Zone.ATTACKING.name]
        if self.target_card_id not in supporting.card_ids and self.target_card_id not in attacking.card_ids:
            return ValidationResult(valid=False, error="Target card must be in an active zone", error_code="INVALID_TARGET")
        assoc_card = state.get_card(self.association_card_id)
        if not assoc_card or not assoc_card.association_ids:
            return ValidationResult(valid=False, error="Card cannot be used as an association", error_code="NOT_ASSOCIATION_CARD")
        return ValidationResult(valid=True)

    def to_events(self, state: "GameState") -> list[GameEvent]:
        assoc_card = state.get_card(self.association_card_id)
        if not assoc_card:
            return []
        return [CardAssociatedEvent(
            game_id=state.game_id, player_id=self.player_id,
            association_card_id=self.association_card_id, target_card_id=self.target_card_id,
            card_id=assoc_card.card_id, source_zone=assoc_card.zone,
        )]

    @classmethod
    def get_valid(cls, state: "GameState", player_id: str) -> list[Action]:
        if state.is_first_turn(player_id):
            return []
        player = state.room.players[player_id]
        actions = []
        sources = player.zones[Zone.HAND.name].card_ids + player.zones[Zone.SUPPORTING.name].card_ids
        for assoc_id in sources:
            assoc_card = state.get_card(assoc_id)
            if assoc_card and assoc_card.association_ids:
                for target_id in player.get_active_cards():
                    if target_id != assoc_id:
                        actions.append(cls(player_id=player_id, association_card_id=assoc_id, target_card_id=target_id))
        return actions
