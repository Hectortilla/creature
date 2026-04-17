"""
Action to Event Generator

Transforms validated actions into events with computed data.
This module does NOT mutate state - it only produces events that describe
what should happen as a result of an action.

Pipeline:
    Action → Validator → ActionToEventGenerator → Events → Reducer → New State
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from app.models.game.enums import Zone, TurnPhase, GameStatus, DamageType
from app.models.game.events import (
    GameEvent,
    CardDrawnEvent,
    CardMovedEvent,
    CardPlayedEvent,
    CardPromotedEvent,
    CardSwappedEvent,
    CardAssociatedEvent,
    CardEvolvedEvent,
    AttackDeclaredEvent,
    DamageDealtEvent,
    CardDestroyedEvent,
    ElementsConsumedEvent,
    ElementsRestoredEvent,
    TurnStartedEvent,
    TurnEndedEvent,
    PhaseChangedEvent,
    GameStartedEvent,
    GameEndedEvent,
    NoDefenderEvent,
)
from app.game.actions import *
from app.game.elements import calculate_damage
from app.game.effects import get_passive_stat_modifiers

if TYPE_CHECKING:
    from app.models.game.state import GameState
    from app.models.game.card import GameCard


class ActionToEventGenerator:
    """
    Transforms actions into events.
    
    The generator reads the current state and produces events that describe
    what should happen. It does NOT modify the state - that's the reducer's job.
    """
    
    def create(self, state: "GameState", action: Action) -> list[GameEvent]:
        """
        Create events from an action.
        
        Args:
            state: Current game state (read-only)
            action: Validated action to transform
        
        Returns:
            List of events to be applied by the reducer
        """
        if isinstance(action, DrawAction):
            return self._create_draw_events(state, action)
        elif isinstance(action, PlayCardAction):
            return self._create_play_card_events(state, action)
        elif isinstance(action, MultiPlayCardAction):
            return self._create_multi_play_card_events(state, action)
        elif isinstance(action, PromoteAction):
            return self._create_promote_events(state, action)
        elif isinstance(action, SwapAction):
            return self._create_swap_events(state, action)
        elif isinstance(action, MultiSwapAction):
            return self._create_multi_swap_events(state, action)
        elif isinstance(action, AssociationAction):
            return self._create_association_events(state, action)
        elif isinstance(action, EvolutionAction):
            return self._create_evolution_events(state, action)
        elif isinstance(action, AttackAction):
            return self._create_attack_events(state, action)
        elif isinstance(action, PassPhaseAction):
            return self._create_pass_events(state, action)
        elif isinstance(action, ForceDefendAction):
            return self._create_force_defend_events(state, action)
        elif isinstance(action, ConcedeAction):
            return self._create_concede_events(state, action)
        
        return []
    
    def _create_draw_events(self, state: "GameState", action: DrawAction) -> list[GameEvent]:
        """Create draw events."""
        events = []
        player = state.room.get_player(action.player_id)
        deck = player.zones[Zone.DECK]
        
        for i in range(min(action.count, len(deck.card_ids))):
            instance_id = deck.card_ids[i]
            card = state.get_card(instance_id)
            
            events.append(CardDrawnEvent(
                game_id=state.game_id,
                player_id=action.player_id,
                instance_id=instance_id,
                card_id=card.card_id if card else 0,
                cards_remaining=len(deck.card_ids) - i - 1,
            ))
        
        return events
    
    def _create_play_card_events(self, state: "GameState", action: PlayCardAction) -> list[GameEvent]:
        """Create play card events."""
        events = []
        card = state.get_card(action.instance_id)
        
        if card:
            events.append(CardPlayedEvent(
                game_id=state.game_id,
                player_id=action.player_id,
                instance_id=action.instance_id,
                card_id=card.card_id,
                card_name=card.name,
            ))
        
        return events
    
    def _create_multi_play_card_events(self, state: "GameState", action: MultiPlayCardAction) -> list[GameEvent]:
        """Create multi play card events."""
        events = []
        
        for instance_id in action.instance_ids:
            card = state.get_card(instance_id)
            if card:
                events.append(CardPlayedEvent(
                    game_id=state.game_id,
                    player_id=action.player_id,
                    instance_id=instance_id,
                    card_id=card.card_id,
                    card_name=card.name,
                ))
        
        return events
    
    def _create_promote_events(self, state: "GameState", action: PromoteAction) -> list[GameEvent]:
        """Create promote events."""
        events = []
        card = state.get_card(action.instance_id)
        
        if card:
            events.append(CardPromotedEvent(
                game_id=state.game_id,
                player_id=action.player_id,
                instance_id=action.instance_id,
                card_id=card.card_id,
                card_name=card.name,
            ))
        
        return events
    
    def _create_swap_events(self, state: "GameState", action: SwapAction) -> list[GameEvent]:
        """Create swap events."""
        events = []
        
        events.append(CardSwappedEvent(
            game_id=state.game_id,
            player_id=action.player_id,
            supporting_card_id=action.supporting_card_id,
            attacking_card_id=action.attacking_card_id,
        ))
        
        return events
    
    def _create_multi_swap_events(self, state: "GameState", action: MultiSwapAction) -> list[GameEvent]:
        """Create multi swap events."""
        events = []
        
        for supporting_id, attacking_id in action.swaps:
            events.append(CardSwappedEvent(
                game_id=state.game_id,
                player_id=action.player_id,
                supporting_card_id=supporting_id,
                attacking_card_id=attacking_id,
            ))
        
        return events
    
    def _create_association_events(self, state: "GameState", action: AssociationAction) -> list[GameEvent]:
        """Create association events."""
        events = []
        assoc_card = state.get_card(action.association_card_id)
        
        if assoc_card:
            events.append(CardAssociatedEvent(
                game_id=state.game_id,
                player_id=action.player_id,
                association_card_id=action.association_card_id,
                target_card_id=action.target_card_id,
                card_id=assoc_card.card_id,
                source_zone=assoc_card.zone,
            ))
        
        return events
    
    def _create_evolution_events(self, state: "GameState", action: EvolutionAction) -> list[GameEvent]:
        """Create evolution events."""
        events = []
        base_card = state.get_card(action.target_card_id)
        evo_card = state.get_card(action.evolution_card_id)
        
        if base_card and evo_card:
            events.append(CardEvolvedEvent(
                game_id=state.game_id,
                player_id=action.player_id,
                base_card_id=action.target_card_id,
                evolution_card_id=action.evolution_card_id,
                card_id=evo_card.card_id,
                base_card_name=base_card.name,
                evolution_card_name=evo_card.name,
            ))
        
        return events
    
    def _create_attack_events(self, state: "GameState", action: AttackAction) -> list[GameEvent]:
        """
        Create attack events.
        
        This is the most complex as it involves:
        1. Checking for no defenders
        2. Calculating damage
        3. Determining destruction
        """
        events = []
        player = state.room.get_player(action.player_id)
        opponent = state.room.get_opponent(action.player_id)
        attacker = state.get_card(action.attacker_id)
        
        if not attacker:
            return events
        
        # Get the attack definition
        attack = None
        for atk in attacker.attacks:
            if atk.attack_id == action.attack_id:
                attack = atk
                break
        
        if not attack:
            return events
        
        # Check for no defenders (No Defenders Rule)
        if len(opponent.zones[Zone.ATTACKING].card_ids) == 0:
            if len(opponent.zones[Zone.SUPPORTING].card_ids) > 0:
                # Must force defend — store pending attack so it can resume
                events.append(NoDefenderEvent(
                    game_id=state.game_id,
                    defender_id=opponent.player_id,
                    attacker_id=action.player_id,
                    must_defend=True,
                    game_lost=False,
                    pending_attacker_card_id=action.attacker_id,
                    pending_attack_id=action.attack_id,
                    pending_attacker_owner_id=action.player_id,
                ))
                return events
            else:
                # No cards at all - game lost
                events.append(NoDefenderEvent(
                    game_id=state.game_id,
                    defender_id=opponent.player_id,
                    attacker_id=action.player_id,
                    must_defend=False,
                    game_lost=True,
                ))
                events.append(GameEndedEvent(
                    game_id=state.game_id,
                    winner_id=action.player_id,
                    loser_id=opponent.player_id,
                    reason="No defenders available",
                ))
                return events
        
        target = state.get_card(action.target_card_id)
        if not target:
            return events
        
        # Consume elements event (using 'necessary_force' matching AttackBase)
        element_costs = {cost.element_id: cost.amount for cost in attack.necessary_force}
        if element_costs:
            events.append(ElementsConsumedEvent(
                game_id=state.game_id,
                player_id=action.player_id,
                elements=element_costs,
                for_attack_id=attack.attack_id,
            ))
        
        # Attack declared event
        events.append(AttackDeclaredEvent(
            game_id=state.game_id,
            attacker_owner_id=action.player_id,
            attacker_id=action.attacker_id,
            target_id=action.target_card_id,
            attack_id=attack.attack_id,
            attack_name=attack.name,
        ))
        
        # Calculate damage (include passive stat modifiers from active skills)
        attacker_mods = get_passive_stat_modifiers(state, attacker)
        target_mods = get_passive_stat_modifiers(state, target)
        effect_mod = attacker_mods["attack_bonus"] - target_mods["defense_bonus"]
        damage_calc = calculate_damage(attack, attacker, target, effect_modifier=effect_mod)
        
        # Damage to target (using 'type' matching AttackBase)
        if damage_calc.final_damage > 0:
            events.append(DamageDealtEvent(
                game_id=state.game_id,
                source_id=action.attacker_id,
                target_id=action.target_card_id,
                damage_type=attack.type,
                base_damage=damage_calc.base_damage,
                element_bonus=damage_calc.element_bonus,
                defense_reduction=damage_calc.defense_value,
                final_damage=damage_calc.final_damage,
                remaining_health=target.current_health - damage_calc.final_damage,
            ))
            
            # Check destruction
            if target.current_health - damage_calc.final_damage <= 0:
                events.append(CardDestroyedEvent(
                    game_id=state.game_id,
                    instance_id=action.target_card_id,
                    owner_id=target.owner_id,
                    card_name=target.name,
                    destroyed_by=action.attacker_id,
                ))
        
        # Reflected damage to attacker
        if damage_calc.reflected_damage > 0:
            events.append(DamageDealtEvent(
                game_id=state.game_id,
                source_id=action.target_card_id,
                target_id=action.attacker_id,
                damage_type=attack.type,
                base_damage=0,
                element_bonus=0,
                defense_reduction=0,
                final_damage=damage_calc.reflected_damage,
                remaining_health=attacker.current_health - damage_calc.reflected_damage,
            ))
            
            # Check attacker destruction
            if attacker.current_health - damage_calc.reflected_damage <= 0:
                events.append(CardDestroyedEvent(
                    game_id=state.game_id,
                    instance_id=action.attacker_id,
                    owner_id=attacker.owner_id,
                    card_name=attacker.name,
                    destroyed_by=action.target_card_id,
                ))
        
        return events
    
    def _create_pass_events(self, state: "GameState", action: PassPhaseAction) -> list[GameEvent]:
        """Create pass events - determine next phase or turn."""
        events = []
        current_phase = state.current_phase
        player = state.room.get_player(action.player_id)
        
        next_phase = current_phase.next_phase()
        
        # Skip phases that have no valid actions
        while next_phase and self._should_skip_phase(state, next_phase, action.player_id):
            next_phase = next_phase.next_phase()
        
        if next_phase:
            # Advance to next phase
            events.append(PhaseChangedEvent(
                game_id=state.game_id,
                player_id=action.player_id,
                from_phase=current_phase,
                to_phase=next_phase,
            ))
            
            # If next is draw phase (new turn for same player), add draw events
            if next_phase == TurnPhase.DRAW:
                draw_count = state.config.initial_draw if player.turn_count == 0 else state.config.normal_draw
                deck = player.zones[Zone.DECK]
                for i in range(min(draw_count, len(deck.card_ids))):
                    instance_id = deck.card_ids[i]
                    card = state.get_card(instance_id)
                    events.append(CardDrawnEvent(
                        game_id=state.game_id,
                        player_id=action.player_id,
                        instance_id=instance_id,
                        card_id=card.card_id if card else 0,
                        cards_remaining=len(deck.card_ids) - i - 1,
                    ))
        else:
            # End of turn, switch to next player
            next_player_id = self._get_next_player(state, action.player_id)
            next_player = state.room.get_player(next_player_id)
            
            # End current turn
            events.append(TurnEndedEvent(
                game_id=state.game_id,
                player_id=action.player_id,
                turn_number=state.turn_number,
            ))
            
            # Restore elements for next player
            events.append(ElementsRestoredEvent(
                game_id=state.game_id,
                player_id=next_player_id,
                elements=dict(next_player.element_pool.max_elements),
            ))
            
            # Start next turn
            events.append(TurnStartedEvent(
                game_id=state.game_id,
                player_id=next_player_id,
                turn_number=state.turn_number + 1,
                is_first_turn=next_player.turn_count == 0,
            ))
            
            # Draw phase
            draw_count = state.config.initial_draw if next_player.turn_count == 0 else state.config.normal_draw
            deck = next_player.zones[Zone.DECK]
            for i in range(min(draw_count, len(deck.card_ids))):
                instance_id = deck.card_ids[i]
                card = state.get_card(instance_id)
                events.append(CardDrawnEvent(
                    game_id=state.game_id,
                    player_id=next_player_id,
                    instance_id=instance_id,
                    card_id=card.card_id if card else 0,
                    cards_remaining=len(deck.card_ids) - i - 1,
                ))
            
            # Advance to placement phase
            events.append(PhaseChangedEvent(
                game_id=state.game_id,
                player_id=next_player_id,
                from_phase=TurnPhase.DRAW,
                to_phase=TurnPhase.PLACEMENT,
            ))
        
        return events
    
    def _create_force_defend_events(self, state: "GameState", action: ForceDefendAction) -> list[GameEvent]:
        """Create force defend events and resume the pending attack."""
        events = []
        card = state.get_card(action.instance_id)

        if card:
            # Promote the defending card to the attacking zone
            events.append(CardPromotedEvent(
                game_id=state.game_id,
                player_id=action.player_id,
                instance_id=action.instance_id,
                card_id=card.card_id,
                card_name=card.name,
            ))

        # Resume the pending attack against the just-promoted card
        if state.pending_attack and card:
            pending = state.pending_attack
            attacker = state.get_card(pending["attacker_id"])

            attack = None
            if attacker:
                for atk in attacker.attacks:
                    if atk.attack_id == pending["attack_id"]:
                        attack = atk
                        break

            if attacker and attack:
                # Consume elements (they were NOT consumed before the NoDefenderEvent)
                element_costs = {cost.element_id: cost.amount for cost in attack.necessary_force}
                if element_costs:
                    events.append(ElementsConsumedEvent(
                        game_id=state.game_id,
                        player_id=pending["attacker_owner_id"],
                        elements=element_costs,
                        for_attack_id=attack.attack_id,
                    ))

                # Declare the attack
                events.append(AttackDeclaredEvent(
                    game_id=state.game_id,
                    attacker_owner_id=pending["attacker_owner_id"],
                    attacker_id=pending["attacker_id"],
                    target_id=action.instance_id,
                    attack_id=attack.attack_id,
                    attack_name=attack.name,
                ))

                # Calculate damage (include passive modifiers)
                attacker_mods = get_passive_stat_modifiers(state, attacker)
                target_mods = get_passive_stat_modifiers(state, card)
                effect_mod = attacker_mods["attack_bonus"] - target_mods["defense_bonus"]
                damage_calc = calculate_damage(attack, attacker, card, effect_modifier=effect_mod)

                # Damage to target
                if damage_calc.final_damage > 0:
                    events.append(DamageDealtEvent(
                        game_id=state.game_id,
                        source_id=pending["attacker_id"],
                        target_id=action.instance_id,
                        damage_type=attack.type,
                        base_damage=damage_calc.base_damage,
                        element_bonus=damage_calc.element_bonus,
                        defense_reduction=damage_calc.defense_value,
                        final_damage=damage_calc.final_damage,
                        remaining_health=card.current_health - damage_calc.final_damage,
                    ))

                    if card.current_health - damage_calc.final_damage <= 0:
                        events.append(CardDestroyedEvent(
                            game_id=state.game_id,
                            instance_id=action.instance_id,
                            owner_id=card.owner_id,
                            card_name=card.name,
                            destroyed_by=pending["attacker_id"],
                        ))

                # Reflected damage to attacker
                if damage_calc.reflected_damage > 0:
                    events.append(DamageDealtEvent(
                        game_id=state.game_id,
                        source_id=action.instance_id,
                        target_id=pending["attacker_id"],
                        damage_type=attack.type,
                        base_damage=0,
                        element_bonus=0,
                        defense_reduction=0,
                        final_damage=damage_calc.reflected_damage,
                        remaining_health=attacker.current_health - damage_calc.reflected_damage,
                    ))

                    if attacker.current_health - damage_calc.reflected_damage <= 0:
                        events.append(CardDestroyedEvent(
                            game_id=state.game_id,
                            instance_id=pending["attacker_id"],
                            owner_id=attacker.owner_id,
                            card_name=attacker.name,
                            destroyed_by=action.instance_id,
                        ))

        return events
    
    def _create_concede_events(self, state: "GameState", action: ConcedeAction) -> list[GameEvent]:
        """Create concede events."""
        events = []
        opponent = state.room.get_opponent(action.player_id)
        
        events.append(GameEndedEvent(
            game_id=state.game_id,
            winner_id=opponent.player_id,
            loser_id=action.player_id,
            reason="Player conceded",
        ))
        
        return events
    
    def _should_skip_phase(self, state: "GameState", phase: TurnPhase, player_id: str) -> bool:
        """Check if a phase should be skipped."""
        player = state.room.get_player(player_id)
        
        if phase == TurnPhase.PROMOTION:
            # Skip if no promotable cards or attacking zone full
            attacking = player.zones[Zone.ATTACKING]
            if attacking.is_full:
                return True
            supporting = player.zones[Zone.SUPPORTING]
            for card_id in supporting.card_ids:
                card = state.get_card(card_id)
                if card and card.can_promote:
                    return False
            return True
        
        if phase == TurnPhase.SWAP:
            supporting = player.zones[Zone.SUPPORTING]
            attacking = player.zones[Zone.ATTACKING]
            return len(supporting.card_ids) == 0 or len(attacking.card_ids) == 0
        
        if phase == TurnPhase.ASSOCIATION:
            return state.is_first_turn(player_id)

        if phase == TurnPhase.EVOLUTION:
            if state.is_first_turn(player_id) or state.is_second_turn(player_id):
                return True
            hand = player.zones[Zone.HAND]
            for card_id in hand.card_ids:
                card = state.get_card(card_id)
                if card and card.is_evolution:
                    return False
            return True

        if phase == TurnPhase.ATTACK:
            if state.is_first_turn(player_id):
                return True
            attacking = player.zones[Zone.ATTACKING]
            return len(attacking.card_ids) == 0
        
        return False
    
    def _get_next_player(self, state: "GameState", current_player_id: str) -> str:
        """Get the next player in turn order."""
        player_ids = list(state.room.players.keys())
        current_index = player_ids.index(current_player_id)
        next_index = (current_index + 1) % len(player_ids)
        return player_ids[next_index]

