"""
Game State Models

Core game state models including configuration and full game state.
"""

from __future__ import annotations

import uuid
from typing import Any, Optional
from datetime import datetime

from pydantic import Field, field_serializer

from app.models.game.base import GameBaseModel
from app.models.game.enums import Zone, TurnPhase, GameStatus
from app.models.game.card import GameCard
from app.models.game.player import PlayerState


class GameConfiguration(GameBaseModel):
    """
    Configuration options for a game.
    """
    deck_size: int = 22
    initial_draw: int = 4
    normal_draw: int = 1
    supporting_zone_size: int = 3
    attacking_zone_size: int = 2


class GameState(GameBaseModel):
    """
    Complete state of a game.
    """
    game_id: str
    players: dict[str, PlayerState]
    cards: dict[str, GameCard] = {}
    active_player_id: Optional[str] = None
    turn_number: int = 0
    current_phase: TurnPhase = TurnPhase.DRAW
    status: GameStatus = GameStatus.WAITING
    winner_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    event_log: list[dict[str, Any]] = []
    pending_action: Optional[str] = None
    config: GameConfiguration = Field(default_factory=GameConfiguration)
    
    @field_serializer('current_phase')
    def serialize_phase(self, value: TurnPhase) -> str:
        return value.name
    
    @field_serializer('status')
    def serialize_status(self, value: GameStatus) -> str:
        return value.name
    
    @field_serializer('created_at')
    def serialize_created_at(self, value: datetime) -> str:
        return value.isoformat()
    
    @classmethod
    def create(cls, player1_id: str, player1_name: str,
               player2_id: str, player2_name: str,
               config: Optional[GameConfiguration] = None) -> "GameState":
        """Factory method to create a new game."""
        return cls(
            game_id=str(uuid.uuid4()),
            players={
                player1_id: PlayerState(player_id=player1_id, name=player1_name),
                player2_id: PlayerState(player_id=player2_id, name=player2_name),
            },
            config=config or GameConfiguration(),
        )
    
    def get_player(self, player_id: str) -> PlayerState:
        """Get a player's state."""
        return self.players[player_id]
    
    def get_active_player(self) -> Optional[PlayerState]:
        """Get the active player's state."""
        if self.active_player_id:
            return self.players[self.active_player_id]
        return None
    
    def get_opponent(self, player_id: str) -> PlayerState:
        """Get the opponent of a given player."""
        for pid, player in self.players.items():
            if pid != player_id:
                return player
        raise ValueError(f"No opponent found for player {player_id}")
    
    def get_card(self, instance_id: str) -> Optional[GameCard]:
        """Get a card by instance ID."""
        return self.cards.get(instance_id)
    
    def get_cards_in_zone(self, player_id: str, zone: Zone) -> list[GameCard]:
        """Get all cards in a specific zone for a player."""
        zone_state = self.players[player_id].zones[zone.name]
        return [self.cards[cid] for cid in zone_state.card_ids if cid in self.cards]
    
    def add_card(self, card: GameCard) -> None:
        """Add a card to the game."""
        self.cards[card.instance_id] = card
        player = self.players[card.owner_id]
        player.zones[card.zone.name].add_card(card.instance_id)
    
    def move_card(self, card_id: str, to_zone: Zone) -> bool:
        """Move a card to a different zone. Returns False if not possible."""
        card = self.cards.get(card_id)
        if not card:
            return False
        
        player = self.players[card.owner_id]
        from_zone = card.zone
        
        if not player.zones[from_zone.name].remove_card(card_id):
            return False
        
        if not player.zones[to_zone.name].add_card(card_id):
            player.zones[from_zone.name].add_card(card_id)
            return False
        
        card.zone = to_zone
        card.turns_in_zone = 0
        return True
    
    def is_first_turn(self, player_id: str) -> bool:
        """Check if this is the first turn for a player."""
        return self.players[player_id].turn_count == 0
    
    def is_second_turn(self, player_id: str) -> bool:
        """Check if this is the second turn for a player."""
        return self.players[player_id].turn_count == 1
    
    def recalculate_elements(self, player_id: str) -> None:
        """Recalculate element pool for a player based on their active cards."""
        player = self.players[player_id]
        active_cards = [
            self.cards[cid] for cid in player.get_active_cards()
            if cid in self.cards
        ]
        player.element_pool.recalculate_from_cards(active_cards)
    
    def log_event(self, event_data: dict[str, Any]) -> None:
        """Add an event to the event log."""
        event_data["timestamp"] = datetime.utcnow().isoformat()
        event_data["turn"] = self.turn_number
        event_data["phase"] = self.current_phase.name
        self.event_log.append(event_data)
    
    def check_game_end(self) -> Optional[str]:
        """
        Check if the game has ended.
        Returns the winner's player_id if game is over, None otherwise.
        """
        for player_id, player in self.players.items():
            total_cards = (
                len(player.zones[Zone.DECK.name].card_ids) +
                len(player.zones[Zone.HAND.name].card_ids) +
                len(player.get_active_cards())
            )
            if total_cards == 0:
                opponent = self.get_opponent(player_id)
                return opponent.player_id
        return None


__all__ = [
    "GameConfiguration",
    "GameState",
]

