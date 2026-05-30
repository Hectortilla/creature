from __future__ import annotations

from typing import TYPE_CHECKING

from app.models.game.enums import Zone, TurnPhase
from app.models.game.events import GameEvent, CardAssociatedEvent
from app.game.actions.base import Action
from app.game.effects import (
    association_allows_direct_from_hand,
    associations_allowed,
    get_association_limit,
    validate_association_target,
)

if TYPE_CHECKING:
    from app.models.game.state import GameState
    from app.game.validators import ValidationResult


class AssociationAction(Action):
    action_type: str = "associate"
    valid_phases: list[TurnPhase] | None = [TurnPhase.ASSOCIATION]
    association_card_id: str = ""
    target_card_id: str = ""
    swap_with_supporting_card_id: str = ""

    def validate(self, state: "GameState") -> "ValidationResult":
        from app.game.validators import ValidationResult
        player = state.room.get_player(self.player_id)
        if state.is_first_turn(self.player_id):
            return ValidationResult(valid=False, error="Cannot associate cards on first turn", error_code="FIRST_TURN_RESTRICTION")
        if self.association_card_id == self.target_card_id:
            return ValidationResult(valid=False, error="Cannot associate a card with itself", error_code="SELF_ASSOCIATION")
        hand = player.zones[Zone.HAND.name]
        supporting = player.zones[Zone.SUPPORTING.name]
        assoc_card = state.get_card(self.association_card_id)
        direct_from_hand = bool(assoc_card and association_allows_direct_from_hand(assoc_card))
        if self.association_card_id not in supporting.card_ids and not (direct_from_hand and self.association_card_id in hand.card_ids):
            return ValidationResult(valid=False, error="Association card must be in hand or supporting zone", error_code="INVALID_ASSOCIATION_SOURCE")
        attacking = player.zones[Zone.ATTACKING.name]
        if self.target_card_id not in supporting.card_ids and self.target_card_id not in attacking.card_ids:
            return ValidationResult(valid=False, error="Target card must be in an active zone", error_code="INVALID_TARGET")
        if not assoc_card or not assoc_card.association_ids:
            return ValidationResult(valid=False, error="Card cannot be used as an association", error_code="NOT_ASSOCIATION_CARD")
        target_card = state.get_card(self.target_card_id)
        if not target_card:
            return ValidationResult(valid=False, error="Target card not found", error_code="TARGET_NOT_FOUND")
        if not associations_allowed(state, target_card):
            return ValidationResult(valid=False, error="Associations are forbidden on this card", error_code="ASSOCIATIONS_FORBIDDEN")
        if len(target_card.associations) >= get_association_limit(state, target_card):
            return ValidationResult(valid=False, error="Association limit reached", error_code="ASSOCIATION_LIMIT_REACHED")
        errors = validate_association_target(state, assoc_card, target_card)
        if errors:
            return ValidationResult(valid=False, error=errors[0], error_code="ASSOCIATION_TARGET_FILTER")
        if self.swap_with_supporting_card_id:
            if target_card.zone != Zone.ATTACKING:
                return ValidationResult(valid=False, error="Swap association target must be in attacking zone", error_code="INVALID_SWAP_ASSOCIATION_TARGET")
            if self.swap_with_supporting_card_id not in supporting.card_ids:
                return ValidationResult(valid=False, error="Swap card must be in supporting zone", error_code="INVALID_SWAP_CARD")
        return ValidationResult(valid=True)

    def to_events(self, state: "GameState") -> list[GameEvent]:
        assoc_card = state.get_card(self.association_card_id)
        if not assoc_card:
            return []
        return [CardAssociatedEvent(
            game_id=state.game_id, player_id=self.player_id,
            association_card_id=self.association_card_id, target_card_id=self.target_card_id,
            card_id=assoc_card.card_id, source_zone=assoc_card.zone,
            swap_with_supporting_card_id=self.swap_with_supporting_card_id,
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
                if assoc_id in player.zones[Zone.HAND.name].card_ids and not association_allows_direct_from_hand(assoc_card):
                    continue
                for target_id in player.get_active_cards():
                    target = state.get_card(target_id)
                    if not target or target_id == assoc_id:
                        continue
                    if not associations_allowed(state, target):
                        continue
                    if len(target.associations) >= get_association_limit(state, target):
                        continue
                    if validate_association_target(state, assoc_card, target):
                        continue
                    swap_ids = [""]
                    if association_allows_direct_from_hand(assoc_card) and target.zone == Zone.ATTACKING:
                        swap_ids = [
                            cid for cid in player.zones[Zone.SUPPORTING.name].card_ids
                            if cid != assoc_id and cid != target_id
                        ] or [""]
                    for swap_id in swap_ids:
                        actions.append(cls(player_id=player_id, association_card_id=assoc_id, target_card_id=target_id, swap_with_supporting_card_id=swap_id))
        return actions
