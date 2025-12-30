"""
Game Engine

Stateless coordinator that orchestrates the game pipeline:
    Action → Validator → Evaluator → Events → EventLoop → Reducer → New State

The engine does NOT hold any state - it just coordinates the flow.
All game state is passed in and returned.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Optional

from app.models.game import (
    Zone,
    TurnPhase,
    GameStatus,
    DamageType,
    GameState,
    GameCard,
    ElementContribution,
    AttackDefinition,
    GameConfiguration,
    GameEvent,
    GameStartedEvent,
    GameEndedEvent,
    TurnStartedEvent,
    PhaseChangedEvent,
    ElementsRestoredEvent,
)
from app.game.actions import (
    Action,
    DrawAction,
    PassPhaseAction,
    ConcedeAction,
    ForceDefendAction,
    PlayCardAction,
    PromoteAction,
    SwapAction,
    AssociationAction,
    EvolutionAction,
    AttackAction,
)
from app.game.validators import RuleValidator
from app.game.event_generator import ActionToEventGenerator
from app.game.event_loop import EventLoop
from app.game.reducer import apply_event


@dataclass
class ActionResult:
    """
    Result of processing an action.
    
    Attributes:
        success: Whether the action was successful
        events: All events generated (including triggered effects)
        error: Error message if action failed
        game_over: Whether the game ended
        winner_id: ID of winner if game ended
        state: The new game state after processing
        valid_actions: Valid actions for the acting player after this action
    """
    success: bool
    events: list[GameEvent] = field(default_factory=list)
    error: Optional[str] = None
    game_over: bool = False
    winner_id: Optional[str] = None
    state: Optional[GameState] = None
    valid_actions: list[dict[str, Any]] = field(default_factory=list)


class GameEngine:
    """
    Stateless game engine that coordinates the pipeline.
    
    Pipeline:
        Action → Validator → Evaluator → Events → EventLoop → Reducer → New State
    
    The engine is stateless - create a new one each time or reuse the same instance.
    All game data lives in GameState which is passed in and returned.
    """
    
    def __init__(self, config: Optional[GameConfiguration] = None):
        self.config = config or GameConfiguration()
        self.validator = RuleValidator()
        self.event_generator = ActionToEventGenerator()
        self.event_loop = EventLoop()
    
    def create_game(
        self,
        player1_id: str,
        player1_name: str,
        player2_id: str,
        player2_name: str,
        player1_deck: list[dict[str, Any]],
        player2_deck: list[dict[str, Any]],
    ) -> GameState:
        """
        Create a new game state with decks set up.
        
        Returns:
            Initialized GameState (status=STARTING)
        """
        state = GameState.create(player1_id, player1_name, player2_id, player2_name, self.config)
        
        # Create cards for each player
        self._setup_deck(state, player1_id, player1_deck)
        self._setup_deck(state, player2_id, player2_deck)
        
        # Shuffle decks
        for player in state.players.values():
            random.shuffle(player.zones[Zone.DECK].card_ids)
        
        state.status = GameStatus.STARTING
        return state
    
    def _setup_deck(self, state: GameState, player_id: str, deck_data: list[dict[str, Any]]) -> None:
        """Setup a player's deck from card data."""
        for card_data in deck_data:
            card = self._create_game_card(card_data, player_id)
            card.zone = Zone.DECK
            state.cards[card.instance_id] = card
            state.players[player_id].zones[Zone.DECK].add_card(card.instance_id)
    
    def _create_game_card(self, card_data: dict[str, Any], owner_id: str) -> GameCard:
        """Create a GameCard from card data dict."""
        attacks = []
        for attack_data in card_data.get("attacks", []):
            necessary_force = [
                ElementContribution(element_id=e["element_id"], amount=e["amount"])
                for e in attack_data.get("necessary_force", [])
            ]
            
            attack_type = DamageType.PHYSICAL
            if attack_data.get("type", "").lower() == "magical":
                attack_type = DamageType.MAGICAL
            
            attacks.append(AttackDefinition(
                attack_id=attack_data["id"],
                name=attack_data["name"],
                damage=attack_data.get("damage", 0),
                type=attack_type,
                element_id=attack_data.get("element_id", 0),
                necessary_force=necessary_force,
                effect=attack_data.get("effect"),
                description=attack_data.get("description"),
                dice_rolls=attack_data.get("dice_rolls"),
            ))
        
        element_contribution = []
        for contrib in card_data.get("element_contribution", []):
            element_contribution.append(
                ElementContribution(element_id=contrib["element_id"], amount=contrib["amount"])
            )
        
        # Default: contribute 1 of each element the card has
        if not element_contribution:
            for elem_id in card_data.get("element_ids", []):
                element_contribution.append(ElementContribution(element_id=elem_id, amount=1))
        
        return GameCard.create(
            card_id=card_data["id"],
            owner_id=owner_id,
            name=card_data["name"],
            health=card_data.get("health", 10),
            physical_defence=card_data.get("physical_defence", 0),
            magic_defence=card_data.get("magic_defence", 0),
            element_ids=card_data.get("element_ids", []),
            element_contribution=element_contribution,
            attacks=attacks,
            skill_ids=card_data.get("skill_ids", []),
            association_ids=card_data.get("association_ids", []),
            is_evolution=card_data.get("is_evolution", False),
            evolves_from_id=card_data.get("evolves_from_id"),
        )
    
    def start_game(self, state: GameState, first_player_id: Optional[str] = None) -> ActionResult:
        """
        Start a game - sets up first turn and draws initial cards.
        
        Args:
            state: Game state (status must be STARTING)
            first_player_id: Who goes first (random if not specified)
        
        Returns:
            ActionResult with new state
        """
        if first_player_id is None:
            first_player_id = random.choice(list(state.players.keys()))
        
        # Build initial events
        initial_events: list[GameEvent] = [
            GameStartedEvent(
                game_id=state.game_id,
                player_ids=list(state.players.keys()),
                first_player_id=first_player_id,
            ),
            TurnStartedEvent(
                game_id=state.game_id,
                player_id=first_player_id,
                turn_number=1,
                is_first_turn=True,
            ),
        ]
        
        # Draw phase events (first turn draws initial_draw amount)
        draw_action = DrawAction(player_id=first_player_id, count=self.config.initial_draw)
        draw_events = self.event_generator.create(state, draw_action)
        initial_events.extend(draw_events)
        
        # Phase change to placement
        initial_events.append(PhaseChangedEvent(
            game_id=state.game_id,
            player_id=first_player_id,
            from_phase=TurnPhase.DRAW,
            to_phase=TurnPhase.PLACEMENT,
        ))
        
        # Process all events through the event loop
        result = self.event_loop.process(state, initial_events)
        
        # Get valid actions for the first player after game start
        valid_actions = []
        if result.final_state:
            valid_actions = self.get_valid_actions(result.final_state, first_player_id)
        
        return ActionResult(
            success=True,
            events=result.all_events,
            state=result.final_state,
            valid_actions=valid_actions,
        )
    
    def process_action(self, state: GameState, action: Action) -> ActionResult:
        """
        Process a player action through the complete pipeline.
        
        Pipeline:
            Action → Validator → Evaluator → Events → EventLoop → Reducer → New State
        
        Args:
            state: Current game state (NOT modified)
            action: Action to process
        
        Returns:
            ActionResult with new state (original state is unchanged)
        """
        # 1. Validate action
        validation = self.validator.validate(state, action)
        if not validation.valid:
            return ActionResult(
                success=False,
                error=validation.error,
                state=state,
            )
        
        try:
            # 2. Transform action to events
            events = self.event_generator.create(state, action)
            
            # 3. Process events through the event loop (applies reducer + triggers effects)
            result = self.event_loop.process(state, events)
            
            # 4. Check for game end
            winner_id = result.final_state.check_game_end()
            game_over = winner_id is not None
            
            if game_over and result.final_state.status != GameStatus.FINISHED:
                loser_id = result.final_state.get_opponent(winner_id).player_id
                end_event = GameEndedEvent(
                    game_id=result.final_state.game_id,
                    winner_id=winner_id,
                    loser_id=loser_id,
                    reason="No cards remaining",
                )
                result.final_state = apply_event(result.final_state, end_event)
                result.all_events.append(end_event)
            
            # Get valid actions for the acting player after the action
            valid_actions = []
            if result.final_state and not game_over:
                valid_actions = self.get_valid_actions(result.final_state, action.player_id)
            
            return ActionResult(
                success=True,
                events=result.all_events,
                game_over=game_over or result.final_state.status == GameStatus.FINISHED,
                winner_id=result.final_state.winner_id,
                state=result.final_state,
                valid_actions=valid_actions,
            )
            
        except Exception as e:
            return ActionResult(
                success=False,
                error=str(e),
                state=state,
            )

    def get_valid_actions(self, state: GameState, player_id: str) -> list[dict[str, Any]]:
        """
        Get all valid actions for a player in the current state.
        
        Returns a list of action dictionaries with action type, parameters, and description.
        """
        valid_actions: list[Action] = []
        player = state.get_player(player_id)
        
        # Can always pass or concede
        valid_actions.append(PassPhaseAction(player_id=player_id))
        valid_actions.append(ConcedeAction(player_id=player_id))
         
        # Check if it's this player's turn
        if state.active_player_id != player_id:
            if state.status == GameStatus.PAUSED and state.pending_action == "force_defend":
                opponent = state.get_opponent(state.active_player_id or "")
                if opponent.player_id == player_id:
                    for card_id in player.zones[Zone.SUPPORTING].card_ids:
                        card = state.get_card(card_id)
                        if card:
                            valid_actions.append(ForceDefendAction(
                                player_id=player_id,
                                card_id=card_id,
                            ))
            return [action.to_dict(state) for action in valid_actions]
        
        phase = state.current_phase
        
        if phase == TurnPhase.PLACEMENT:
            for card_id in player.zones[Zone.HAND].card_ids:
                card = state.get_card(card_id)
                if card and not player.zones[Zone.SUPPORTING].is_full():
                    valid_actions.append(PlayCardAction(
                        player_id=player_id,
                        card_id=card_id,
                    ))
        
        elif phase == TurnPhase.PROMOTION:
            for card_id in player.zones[Zone.SUPPORTING].card_ids:
                card = state.get_card(card_id)
                if card and card.can_promote() and not player.zones[Zone.ATTACKING].is_full():
                    valid_actions.append(PromoteAction(
                        player_id=player_id,
                        card_id=card_id,
                    ))
        
        elif phase == TurnPhase.SWAP:
            for supp_id in player.zones[Zone.SUPPORTING].card_ids:
                for atk_id in player.zones[Zone.ATTACKING].card_ids:
                    valid_actions.append(SwapAction(
                        player_id=player_id,
                        supporting_card_id=supp_id,
                        attacking_card_id=atk_id,
                    ))
        
        elif phase == TurnPhase.ASSOCIATION:
            if not state.is_first_turn(player_id):
                for assoc_id in (player.zones[Zone.HAND].card_ids + 
                                player.zones[Zone.SUPPORTING].card_ids):
                    assoc_card = state.get_card(assoc_id)
                    if assoc_card and assoc_card.association_ids:
                        for target_id in player.get_active_cards():
                            if target_id != assoc_id:
                                valid_actions.append(AssociationAction(
                                    player_id=player_id,
                                    association_card_id=assoc_id,
                                    target_card_id=target_id,
                                ))
        
        elif phase == TurnPhase.EVOLUTION:
            if not state.is_first_turn(player_id) and not state.is_second_turn(player_id):
                for evo_id in player.zones[Zone.HAND].card_ids:
                    evo_card = state.get_card(evo_id)
                    if evo_card and evo_card.is_evolution:
                        for target_id in player.get_active_cards():
                            target_card = state.get_card(target_id)
                            if (target_card and 
                                target_card.can_evolve() and
                                target_card.card_id == evo_card.evolves_from_id):
                                valid_actions.append(EvolutionAction(
                                    player_id=player_id,
                                    evolution_card_id=evo_id,
                                    target_card_id=target_id,
                                ))
        
        elif phase == TurnPhase.ATTACK:
            if not state.is_first_turn(player_id):
                opponent = state.get_opponent(player_id)
                
                for attacker_id in player.zones[Zone.ATTACKING].card_ids:
                    attacker = state.get_card(attacker_id)
                    if attacker and attacker.can_attack():
                        for attack in attacker.attacks:
                            can_afford = all(
                                player.element_pool.get_available(cost.element_id) >= cost.amount
                                for cost in attack.necessary_force
                            )
                            
                            if can_afford:
                                # Add attack for each valid target
                                for target_id in opponent.zones[Zone.ATTACKING].card_ids:
                                    valid_actions.append(AttackAction(
                                        player_id=player_id,
                                        attacker_id=attacker_id,
                                        attack_id=attack.attack_id,
                                        target_card_id=target_id,
                                    ))
                                
                                # If no defenders, can attack with empty target
                                if len(opponent.zones[Zone.ATTACKING].card_ids) == 0:
                                    valid_actions.append(AttackAction(
                                        player_id=player_id,
                                        attacker_id=attacker_id,
                                        attack_id=attack.attack_id,
                                        target_card_id="",
                                    ))
        
        return [action.to_dict(state) for action in valid_actions]


# Singleton engine instance - since it's stateless, one instance is enough
_engine: Optional[GameEngine] = None


def get_engine(config: Optional[GameConfiguration] = None) -> GameEngine:
    """Get or create the game engine singleton."""
    global _engine
    if _engine is None:
        _engine = GameEngine(config)
    return _engine
