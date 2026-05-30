"""
Rule Validators

Common pre-checks (game status, active player, phase) then delegates
to each action's own validate() method.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from app.models.game.enums import GameStatus
from app.game.actions import Action, ForceDefendAction, ResolveForcedSwapAction, ConcedeAction

if TYPE_CHECKING:
    from app.models.game.state import GameState


@dataclass
class ValidationResult:
    valid: bool
    error: Optional[str] = None
    error_code: Optional[str] = None


class RuleValidator:
    """Validates game actions: common pre-checks + action-specific rules."""

    def validate(self, state: "GameState", action: Action) -> ValidationResult:
        # Game must be in progress (or paused for force defend / concede)
        if state.status != GameStatus.IN_PROGRESS:
            if state.status == GameStatus.PAUSED and not isinstance(action, (ForceDefendAction, ResolveForcedSwapAction, ConcedeAction)):
                return ValidationResult(valid=False, error="Game is paused, waiting for forced defend action", error_code="GAME_PAUSED")
            elif state.status != GameStatus.PAUSED:
                return ValidationResult(valid=False, error=f"Game is not in progress (status: {state.status.name})", error_code="GAME_NOT_IN_PROGRESS")

        # Must be the player's turn (except force defend and concede)
        if not isinstance(action, (ForceDefendAction, ResolveForcedSwapAction, ConcedeAction)):
            if action.player_id != state.active_player_id:
                return ValidationResult(valid=False, error="It is not your turn", error_code="NOT_YOUR_TURN")

        # Phase check
        if action.valid_phases is not None:
            if state.current_phase not in action.valid_phases:
                return ValidationResult(valid=False, error=f"Cannot perform {action.action_type} during {state.current_phase.name} phase", error_code="WRONG_PHASE")

        # Delegate to the action's own validation
        return action.validate(state)
