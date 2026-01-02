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
from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.game.player import PlayerState
    from app.websocket.models import GameRoom

from app.models.game import (
    Zone,
    TurnPhase,
    GameStatus,
    GameState,
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
        final_players: The updated players dict after processing
        valid_actions: Valid actions for the acting player after this action
    """
    success: bool
    events: list[GameEvent] = field(default_factory=list)
    error: Optional[str] = None
    game_over: bool = False
    winner_id: Optional[str] = None
    state: Optional[GameState] = None
    final_players: Optional[dict[str, PlayerState]] = None
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
        room: "GameRoom"
    ) -> GameState:
        """
        Create a new game state with decks set up.
        
        Returns:
            Initialized GameState (status=STARTING)
        """
        # Create state with room reference
        state = GameState.create(room, self.config)
        # Create cards for each player
        
        # Shuffle decks
        for player in room.players.values():
            state._setup_deck(player)
            player.shuffle_deck()
        
        state.status = GameStatus.STARTING
        return state
    
    def start_game(self, state: GameRoom) -> ActionResult:
        """
        Start a game - sets up first turn and draws initial cards.
        
        Randomly selects the first player from available players.
        
        Args:
            state: Game state (status must be STARTING)
        
        Returns:
            ActionResult with new state
        """
        # Randomly select the first player
        player_ids = list(state.room.players.keys())
        first_player_id = random.choice(player_ids)
        
        # Build initial events
        initial_events: list[GameEvent] = [
            GameStartedEvent(
                game_id=state.game_id,
                player_ids=player_ids,
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
        result = self.event_loop.process(state, state.room.players, initial_events)
        
        # Update room's players reference
        state.room.players = result.final_players
        
        # Get valid actions for the first player after game start
        valid_actions = []
        if result.final_state:
            valid_actions = self.get_valid_actions(result.final_state, first_player_id)
        
        return ActionResult(
            success=True,
            events=result.all_events,
            state=result.final_state,
            final_players=result.final_players,
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
        validation = self.validator.validate(state, state.room.players, action)
        if not validation.valid:
            return ActionResult(
                success=False,
                error=validation.error,
                state=state,
            )
        
        try:
            # 2. Transform action to events
            events = self.event_generator.create(state, state.room.players, action)
            
            # 3. Process events through the event loop (applies reducer + triggers effects)
            result = self.event_loop.process(state, state.room.players, events)
            
            # Update room's players reference
            result.final_state.room.players = result.final_players
            
            # 4. Check for game end
            winner_id = result.final_state.check_game_end()
            game_over = winner_id is not None
            
            if game_over and result.final_state.status != GameStatus.FINISHED:
                # Find opponent
                loser_id = None
                for pid in result.final_players.keys():
                    if pid != winner_id:
                        loser_id = pid
                        break
                if loser_id:
                    end_event = GameEndedEvent(
                        game_id=result.final_state.game_id,
                        winner_id=winner_id,
                        loser_id=loser_id,
                        reason="No cards remaining",
                    )
                    result.final_state, result.final_players = apply_event(result.final_state, result.final_players, end_event)
                    result.final_state.room.players = result.final_players
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
                final_players=result.final_players,
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
        player = state.room.players[player_id]
        
        # Can always pass or concede
        valid_actions.append(PassPhaseAction(player_id=player_id))
        valid_actions.append(ConcedeAction(player_id=player_id))
         
        # Check if it's this player's turn
        if state.active_player_id != player_id:
            if state.status == GameStatus.PAUSED and state.pending_action == "force_defend":
                # Find opponent
                active_opponent = None
                for pid, p in state.room.players.items():
                    if pid != state.active_player_id:
                        active_opponent = p
                        break
                if active_opponent and active_opponent.player_id == player_id:
                    for card_id in player.zones[Zone.SUPPORTING.name].card_ids:
                        card = state.get_card(card_id)
                        if card:
                            valid_actions.append(ForceDefendAction(
                                player_id=player_id,
                                card_id=card_id,
                            ))
            return [action.to_dict(state) for action in valid_actions]
        
        phase = state.current_phase
        
        if phase == TurnPhase.PLACEMENT:
            for card_id in player.zones[Zone.HAND.name].card_ids:
                card = state.get_card(card_id)
                if card and not player.zones[Zone.SUPPORTING.name].is_full():
                    valid_actions.append(PlayCardAction(
                        player_id=player_id,
                        card_id=card_id,
                    ))
        
        elif phase == TurnPhase.PROMOTION:
            for card_id in player.zones[Zone.SUPPORTING.name].card_ids:
                card = state.get_card(card_id)
                if card and card.can_promote() and not player.zones[Zone.ATTACKING.name].is_full():
                    valid_actions.append(PromoteAction(
                        player_id=player_id,
                        card_id=card_id,
                    ))
        
        elif phase == TurnPhase.SWAP:
            for supp_id in player.zones[Zone.SUPPORTING.name].card_ids:
                for atk_id in player.zones[Zone.ATTACKING.name].card_ids:
                    valid_actions.append(SwapAction(
                        player_id=player_id,
                        supporting_card_id=supp_id,
                        attacking_card_id=atk_id,
                    ))
        
        elif phase == TurnPhase.ASSOCIATION:
            if not state.is_first_turn(player_id):
                for assoc_id in (player.zones[Zone.HAND.name].card_ids + 
                                player.zones[Zone.SUPPORTING.name].card_ids):
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
                for evo_id in player.zones[Zone.HAND.name].card_ids:
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
                # Find opponent
                opponent = None
                for pid, p in state.room.players.items():
                    if pid != player_id:
                        opponent = p
                        break
                if not opponent:
                    return [action.to_dict(state) for action in valid_actions]
                
                for attacker_id in player.zones[Zone.ATTACKING.name].card_ids:
                    attacker = state.get_card(attacker_id)
                    if attacker and attacker.can_attack():
                        for attack in attacker.attacks:
                            can_afford = all(
                                player.element_pool.get_available(cost.element_id) >= cost.amount
                                for cost in attack.necessary_force
                            )
                            
                            if can_afford:
                                # Add attack for each valid target
                                for target_id in opponent.zones[Zone.ATTACKING.name].card_ids:
                                    valid_actions.append(AttackAction(
                                        player_id=player_id,
                                        attacker_id=attacker_id,
                                        attack_id=attack.attack_id,
                                        target_card_id=target_id,
                                    ))
                                
                                # If no defenders, can attack with empty target
                                if len(opponent.zones[Zone.ATTACKING.name].card_ids) == 0:
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
