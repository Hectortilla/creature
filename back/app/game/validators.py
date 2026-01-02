"""
Rule Validators

Validates all game actions against the rules for each phase.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from app.models.game import Zone, TurnPhase, GameStatus
from app.game.actions import *
from app.game.elements import can_afford_attack

if TYPE_CHECKING:
    from app.models.game import GameState, GameCard


class ValidationError(Exception):
    """Exception raised when an action fails validation."""
    
    def __init__(self, message: str, code: str = "INVALID_ACTION"):
        self.message = message
        self.code = code
        super().__init__(message)


@dataclass
class ValidationResult:
    """
    Result of a validation check.
    
    Attributes:
        valid: Whether the action is valid
        error: Error message if invalid
        error_code: Error code for programmatic handling
    """
    valid: bool
    error: Optional[str] = None
    error_code: Optional[str] = None


class RuleValidator:
    """
    Validates game actions against the rules.
    
    Performs comprehensive validation including:
    - Phase validity
    - Turn restrictions (first/second turn exceptions)
    - Zone capacity
    - Card eligibility
    - Element costs
    """
    
    def validate(self, state: "GameState", action: Action) -> ValidationResult:
        """
        Validate an action against the current game state.
        
        Args:
            state: Current game state
            action: Action to validate
        
        Returns:
            ValidationResult indicating if action is valid
        
        Raises:
            ValidationError: If action is invalid and raise_on_error is True
        """
        # Check game is in progress
        if state.status != GameStatus.IN_PROGRESS:
            if state.status == GameStatus.PAUSED and not isinstance(action, (ForceDefendAction, ConcedeAction)):
                return ValidationResult(
                    valid=False,
                    error="Game is paused, waiting for forced defend action",
                    error_code="GAME_PAUSED"
                )
            elif state.status != GameStatus.PAUSED:
                return ValidationResult(
                    valid=False,
                    error=f"Game is not in progress (status: {state.status.name})",
                    error_code="GAME_NOT_IN_PROGRESS"
                )
        
        # Check it's the player's turn (except for forced defend and concede)
        if not isinstance(action, (ForceDefendAction, ConcedeAction)):
            if action.player_id != state.active_player_id:
                return ValidationResult(
                    valid=False,
                    error="It is not your turn",
                    error_code="NOT_YOUR_TURN"
                )
        
        # Check phase validity
        if action.valid_phases is not None:
            if state.current_phase not in action.valid_phases:
                return ValidationResult(
                    valid=False,
                    error=f"Cannot perform {action.action_type} during {state.current_phase.name} phase",
                    error_code="WRONG_PHASE"
                )
        
        # Delegate to specific validators
        if isinstance(action, DrawAction):
            return self._validate_draw(state, action)
        elif isinstance(action, PlayCardAction):
            return self._validate_play_card(state, action)
        elif isinstance(action, MultiPlayCardAction):
            return self._validate_multi_play_card(state, action)
        elif isinstance(action, PromoteAction):
            return self._validate_promote(state, action)
        elif isinstance(action, SwapAction):
            return self._validate_swap(state, action)
        elif isinstance(action, MultiSwapAction):
            return self._validate_multi_swap(state, action)
        elif isinstance(action, AssociationAction):
            return self._validate_association(state, action)
        elif isinstance(action, EvolutionAction):
            return self._validate_evolution(state, action)
        elif isinstance(action, AttackAction):
            return self._validate_attack(state, action)
        elif isinstance(action, ForceDefendAction):
            return self._validate_force_defend(state, action)
        elif isinstance(action, PassPhaseAction):
            return self._validate_pass(state, action)
        elif isinstance(action, ConcedeAction):
            return ValidationResult(valid=True)  # Can always concede
        
        return ValidationResult(
            valid=False,
            error=f"Unknown action type: {action.action_type}",
            error_code="UNKNOWN_ACTION"
        )
    
    def _validate_draw(self, state: "GameState", action: DrawAction) -> ValidationResult:
        """Validate draw action."""
        player = state.room.get_player(action.player_id)
        deck = player.zones[Zone.DECK]
        
        if len(deck.card_ids) < action.count:
            return ValidationResult(
                valid=False,
                error=f"Not enough cards in deck (have {len(deck.card_ids)}, need {action.count})",
                error_code="NOT_ENOUGH_CARDS"
            )
        
        return ValidationResult(valid=True)
    
    def _validate_play_card(self, state: "GameState", action: PlayCardAction) -> ValidationResult:
        """Validate playing a card from hand to supporting zone."""
        player = state.room.get_player(action.player_id)
        
        # Check first turn restrictions - can only place, not attack/associate/evolve
        # (but placement is allowed, so this check is OK)
        
        # Check card is in hand
        hand = player.zones[Zone.HAND]
        if action.card_id not in hand.card_ids:
            return ValidationResult(
                valid=False,
                error="Card is not in your hand",
                error_code="CARD_NOT_IN_HAND"
            )
        
        # Check supporting zone has space
        supporting = player.zones[Zone.SUPPORTING]
        if supporting.is_full:
            return ValidationResult(
                valid=False,
                error="Supporting zone is full (max 3 cards)",
                error_code="SUPPORTING_ZONE_FULL"
            )
        
        return ValidationResult(valid=True)
    
    def _validate_multi_play_card(self, state: "GameState", action: MultiPlayCardAction) -> ValidationResult:
        """Validate playing multiple cards."""
        player = state.room.get_player(action.player_id)
        supporting = player.zones[Zone.SUPPORTING]
        hand = player.zones[Zone.HAND]
        
        # Check we have enough slots
        available_slots = supporting.available_slots()
        if len(action.card_ids) > available_slots:
            return ValidationResult(
                valid=False,
                error=f"Not enough slots in supporting zone (have {available_slots}, need {len(action.card_ids)})",
                error_code="NOT_ENOUGH_SLOTS"
            )
        
        # Check all cards are in hand
        for card_id in action.card_ids:
            if card_id not in hand.card_ids:
                return ValidationResult(
                    valid=False,
                    error=f"Card {card_id} is not in your hand",
                    error_code="CARD_NOT_IN_HAND"
                )
        
        # Check for duplicates
        if len(action.card_ids) != len(set(action.card_ids)):
            return ValidationResult(
                valid=False,
                error="Duplicate cards in play action",
                error_code="DUPLICATE_CARDS"
            )
        
        return ValidationResult(valid=True)
    
    def _validate_promote(self, state: "GameState", action: PromoteAction) -> ValidationResult:
        """Validate promoting a card from supporting to attacking zone."""
        player = state.room.get_player(action.player_id)
        
        # Check card is in supporting zone
        supporting = player.zones[Zone.SUPPORTING]
        if action.card_id not in supporting.card_ids:
            return ValidationResult(
                valid=False,
                error="Card is not in supporting zone",
                error_code="CARD_NOT_IN_SUPPORTING"
            )
        
        # Check attacking zone has space
        attacking = player.zones[Zone.ATTACKING]
        if attacking.is_full:
            return ValidationResult(
                valid=False,
                error="Attacking zone is full (max 2 cards)",
                error_code="ATTACKING_ZONE_FULL"
            )
        
        # Check card has spent at least 1 full turn in supporting zone
        card = state.get_card(action.card_id)
        if not card or not card.can_promote():
            return ValidationResult(
                valid=False,
                error="Card must spend at least one full turn in supporting zone before promotion",
                error_code="CARD_NOT_READY"
            )
        
        return ValidationResult(valid=True)
    
    def _validate_swap(self, state: "GameState", action: SwapAction) -> ValidationResult:
        """Validate swapping a supporting card with an attacking card."""
        player = state.room.get_player(action.player_id)
        
        # Check supporting card is in supporting zone
        supporting = player.zones[Zone.SUPPORTING]
        if action.supporting_card_id not in supporting.card_ids:
            return ValidationResult(
                valid=False,
                error="Card is not in supporting zone",
                error_code="CARD_NOT_IN_SUPPORTING"
            )
        
        # Check attacking card is in attacking zone
        attacking = player.zones[Zone.ATTACKING]
        if action.attacking_card_id not in attacking.card_ids:
            return ValidationResult(
                valid=False,
                error="Card is not in attacking zone",
                error_code="CARD_NOT_IN_ATTACKING"
            )
        
        return ValidationResult(valid=True)
    
    def _validate_multi_swap(self, state: "GameState", action: MultiSwapAction) -> ValidationResult:
        """Validate multiple swaps."""
        player = state.room.get_player(action.player_id)
        supporting_zone = player.zones[Zone.SUPPORTING]
        attacking_zone = player.zones[Zone.ATTACKING]
        
        used_supporting = set()
        used_attacking = set()
        
        for supporting_id, attacking_id in action.swaps:
            # Check for duplicates
            if supporting_id in used_supporting:
                return ValidationResult(
                    valid=False,
                    error=f"Card {supporting_id} used in multiple swaps",
                    error_code="DUPLICATE_SWAP"
                )
            if attacking_id in used_attacking:
                return ValidationResult(
                    valid=False,
                    error=f"Card {attacking_id} used in multiple swaps",
                    error_code="DUPLICATE_SWAP"
                )
            
            used_supporting.add(supporting_id)
            used_attacking.add(attacking_id)
            
            # Check cards are in correct zones
            if supporting_id not in supporting_zone.card_ids:
                return ValidationResult(
                    valid=False,
                    error=f"Card {supporting_id} is not in supporting zone",
                    error_code="CARD_NOT_IN_SUPPORTING"
                )
            if attacking_id not in attacking_zone.card_ids:
                return ValidationResult(
                    valid=False,
                    error=f"Card {attacking_id} is not in attacking zone",
                    error_code="CARD_NOT_IN_ATTACKING"
                )
        
        return ValidationResult(valid=True)
    
    def _validate_association(self, state: "GameState", action: AssociationAction) -> ValidationResult:
        """Validate associating a card with another card."""
        player = state.room.get_player(action.player_id)
        
        # Check first turn restriction
        if state.is_first_turn(action.player_id):
            return ValidationResult(
                valid=False,
                error="Cannot associate cards on first turn",
                error_code="FIRST_TURN_RESTRICTION"
            )
        
        # Check association card is in hand or supporting zone
        hand = player.zones[Zone.HAND]
        supporting = player.zones[Zone.SUPPORTING]
        
        if action.association_card_id not in hand.card_ids and action.association_card_id not in supporting.card_ids:
            return ValidationResult(
                valid=False,
                error="Association card must be in hand or supporting zone",
                error_code="INVALID_ASSOCIATION_SOURCE"
            )
        
        # Check target card is in an active zone
        attacking = player.zones[Zone.ATTACKING]
        if action.target_card_id not in supporting.card_ids and action.target_card_id not in attacking.card_ids:
            return ValidationResult(
                valid=False,
                error="Target card must be in an active zone",
                error_code="INVALID_TARGET"
            )
        
        # Check association card has association capability
        assoc_card = state.get_card(action.association_card_id)
        if not assoc_card or not assoc_card.association_ids:
            return ValidationResult(
                valid=False,
                error="Card cannot be used as an association",
                error_code="NOT_ASSOCIATION_CARD"
            )
        
        return ValidationResult(valid=True)
    
    def _validate_evolution(self, state: "GameState", action: EvolutionAction) -> ValidationResult:
        """Validate evolving a card."""
        player = state.room.get_player(action.player_id)
        
        # Check first and second turn restrictions
        if state.is_first_turn(action.player_id):
            return ValidationResult(
                valid=False,
                error="Cannot evolve cards on first turn",
                error_code="FIRST_TURN_RESTRICTION"
            )
        if state.is_second_turn(action.player_id):
            return ValidationResult(
                valid=False,
                error="Cannot evolve cards on second turn",
                error_code="SECOND_TURN_RESTRICTION"
            )
        
        # Check evolution card is in hand
        hand = player.zones[Zone.HAND]
        if action.evolution_card_id not in hand.card_ids:
            return ValidationResult(
                valid=False,
                error="Evolution card must be in hand",
                error_code="CARD_NOT_IN_HAND"
            )
        
        # Check target card is in an active zone
        supporting = player.zones[Zone.SUPPORTING]
        attacking = player.zones[Zone.ATTACKING]
        if action.target_card_id not in supporting.card_ids and action.target_card_id not in attacking.card_ids:
            return ValidationResult(
                valid=False,
                error="Target card must be in an active zone",
                error_code="INVALID_TARGET"
            )
        
        # Check evolution card is actually an evolution
        evo_card = state.get_card(action.evolution_card_id)
        if not evo_card or not evo_card.is_evolution:
            return ValidationResult(
                valid=False,
                error="Card is not an evolution",
                error_code="NOT_EVOLUTION_CARD"
            )
        
        # Check target matches evolution requirement
        target_card = state.get_card(action.target_card_id)
        if not target_card:
            return ValidationResult(
                valid=False,
                error="Target card not found",
                error_code="TARGET_NOT_FOUND"
            )
        
        if target_card.card_id != evo_card.evolves_from_id:
            return ValidationResult(
                valid=False,
                error="Target card does not match evolution requirement",
                error_code="EVOLUTION_MISMATCH"
            )
        
        # Check target has been in active zone for at least 1 turn
        if not target_card.can_evolve():
            return ValidationResult(
                valid=False,
                error="Target card must have been active for at least one full turn",
                error_code="TARGET_NOT_READY"
            )
        
        return ValidationResult(valid=True)
    
    def _validate_attack(self, state: "GameState", action: AttackAction) -> ValidationResult:
        """Validate an attack action."""
        player = state.room.get_player(action.player_id)
        opponent = state.get_opponent(action.player_id)
        
        # Check first turn restriction
        if state.is_first_turn(action.player_id):
            return ValidationResult(
                valid=False,
                error="Cannot attack on first turn",
                error_code="FIRST_TURN_RESTRICTION"
            )
        
        # Check attacker is in attacking zone
        attacking = player.zones[Zone.ATTACKING]
        if action.attacker_id not in attacking.card_ids:
            return ValidationResult(
                valid=False,
                error="Attacker must be in attacking zone",
                error_code="ATTACKER_NOT_IN_ATTACKING"
            )
        
        # Check attacker can attack
        attacker = state.get_card(action.attacker_id)
        if not attacker or not attacker.can_attack():
            return ValidationResult(
                valid=False,
                error="Card cannot attack (already attacked this turn or is associated)",
                error_code="CANNOT_ATTACK"
            )
        
        # Check attack exists on card
        attack = None
        for atk in attacker.attacks:
            if atk.attack_id == action.attack_id:
                attack = atk
                break
        
        if not attack:
            return ValidationResult(
                valid=False,
                error="Card does not have this attack",
                error_code="INVALID_ATTACK"
            )
        
        # Check element costs
        if not can_afford_attack(
            {elem: player.element_pool.get_available(elem) for elem in player.element_pool.elements},
            attack
        ):
            return ValidationResult(
                valid=False,
                error="Not enough elements to perform this attack",
                error_code="INSUFFICIENT_ELEMENTS"
            )
        
        # Check target is in opponent's attacking zone
        opponent_attacking = opponent.zones[Zone.ATTACKING]
        if action.target_card_id not in opponent_attacking.card_ids:
            # Check if opponent has no attackers (No Defenders rule)
            if len(opponent_attacking.card_ids) == 0:
                # This will trigger the forced defend mechanic
                return ValidationResult(valid=True)
            
            return ValidationResult(
                valid=False,
                error="Target must be in opponent's attacking zone",
                error_code="INVALID_TARGET"
            )
        
        # Check target exists
        target = state.get_card(action.target_card_id)
        if not target:
            return ValidationResult(
                valid=False,
                error="Target card not found",
                error_code="TARGET_NOT_FOUND"
            )
        
        return ValidationResult(valid=True)
    
    def _validate_force_defend(self, state: "GameState", action: ForceDefendAction) -> ValidationResult:
        """Validate force defend action."""
        # Check game is paused for force defend
        if state.pending_action != "force_defend":
            return ValidationResult(
                valid=False,
                error="No force defend pending",
                error_code="NO_FORCE_DEFEND"
            )
        
        player = state.room.get_player(action.player_id)
        
        # Check card is in supporting zone
        supporting = player.zones[Zone.SUPPORTING]
        if action.card_id not in supporting.card_ids:
            return ValidationResult(
                valid=False,
                error="Card must be in supporting zone",
                error_code="CARD_NOT_IN_SUPPORTING"
            )
        
        # Check attacking zone has space
        attacking = player.zones[Zone.ATTACKING]
        if attacking.is_full:
            return ValidationResult(
                valid=False,
                error="Attacking zone is full",
                error_code="ATTACKING_ZONE_FULL"
            )
        
        return ValidationResult(valid=True)
    
    def _validate_pass(self, state: "GameState", action: PassPhaseAction) -> ValidationResult:
        """Validate pass action."""
        # Can always pass
        return ValidationResult(valid=True)
