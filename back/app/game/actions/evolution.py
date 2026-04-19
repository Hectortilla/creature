from __future__ import annotations

from typing import TYPE_CHECKING

from app.models.game.enums import Zone, TurnPhase
from app.models.game.events import GameEvent, CardEvolvedEvent
from app.game.actions.base import Action

if TYPE_CHECKING:
    from app.models.game.state import GameState
    from app.game.validators import ValidationResult


class EvolutionAction(Action):
    action_type: str = "evolve"
    valid_phases: list[TurnPhase] | None = [TurnPhase.EVOLUTION]
    evolution_card_id: str = ""
    target_card_id: str = ""

    def validate(self, state: "GameState") -> "ValidationResult":
        from app.game.validators import ValidationResult
        player = state.room.get_player(self.player_id)
        if state.is_first_turn(self.player_id):
            return ValidationResult(valid=False, error="Cannot evolve cards on first turn", error_code="FIRST_TURN_RESTRICTION")
        if state.is_second_turn(self.player_id):
            return ValidationResult(valid=False, error="Cannot evolve cards on second turn", error_code="SECOND_TURN_RESTRICTION")
        hand = player.zones[Zone.HAND.name]
        if self.evolution_card_id not in hand.card_ids:
            return ValidationResult(valid=False, error="Evolution card must be in hand", error_code="CARD_NOT_IN_HAND")
        supporting = player.zones[Zone.SUPPORTING.name]
        attacking = player.zones[Zone.ATTACKING.name]
        if self.target_card_id not in supporting.card_ids and self.target_card_id not in attacking.card_ids:
            return ValidationResult(valid=False, error="Target card must be in an active zone", error_code="INVALID_TARGET")
        evo_card = state.get_card(self.evolution_card_id)
        if not evo_card or not evo_card.is_evolution:
            return ValidationResult(valid=False, error="Card is not an evolution", error_code="NOT_EVOLUTION_CARD")
        target_card = state.get_card(self.target_card_id)
        if not target_card:
            return ValidationResult(valid=False, error="Target card not found", error_code="TARGET_NOT_FOUND")
        if target_card.card_id != evo_card.evolves_from_id:
            return ValidationResult(valid=False, error="Target card does not match evolution requirement", error_code="EVOLUTION_MISMATCH")
        if not target_card.can_evolve:
            return ValidationResult(valid=False, error="Target card must have been active for at least one full turn", error_code="TARGET_NOT_READY")
        return ValidationResult(valid=True)

    def to_events(self, state: "GameState") -> list[GameEvent]:
        base_card = state.get_card(self.target_card_id)
        evo_card = state.get_card(self.evolution_card_id)
        if not base_card or not evo_card:
            return []
        return [CardEvolvedEvent(
            game_id=state.game_id, player_id=self.player_id,
            base_card_id=self.target_card_id, evolution_card_id=self.evolution_card_id,
            card_id=evo_card.card_id, base_card_name=base_card.name, evolution_card_name=evo_card.name,
        )]

    @classmethod
    def get_valid(cls, state: "GameState", player_id: str) -> list[Action]:
        if state.is_first_turn(player_id) or state.is_second_turn(player_id):
            return []
        player = state.room.players[player_id]
        actions = []
        for evo_id in player.zones[Zone.HAND.name].card_ids:
            evo_card = state.get_card(evo_id)
            if evo_card and evo_card.is_evolution:
                for target_id in player.get_active_cards():
                    target_card = state.get_card(target_id)
                    if target_card and target_card.can_evolve and target_card.card_id == evo_card.evolves_from_id:
                        actions.append(cls(player_id=player_id, evolution_card_id=evo_id, target_card_id=target_id))
        return actions
