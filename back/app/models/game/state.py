"""
Game State Models

Core game state models including configuration and full game state.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Annotated, Any, Optional
from datetime import datetime

from pydantic import Field, SkipValidation, field_serializer, computed_field

from app.models.game.base import GameBaseModel
from app.models.game.enums import Zone, TurnPhase, GameStatus
from app.models.game.card import GameCard, GameCardInput
from app.models.game.player import PlayerState

from app.models.game.attack import AttackDefinition
from app.models.game.enums import DamageType
from app.models.game.element import ElementContribution

if TYPE_CHECKING:
    from app.websocket.models import GameRoom

# Fields visible on hidden cards (deck, opponent hand).
# Everything else is zeroed out so new card fields don't leak.
_VISIBLE_HIDDEN_FIELDS = {"instance_id", "owner_id", "zone", "status", "turns_in_zone"}


class GameStateForPlayer(GameBaseModel):
    """
    Read schema representing the game state payload sent to a player.

    This matches the output of GameState.serialize_for_player() and includes
    the cards and players maps that are excluded from the base GameState schema.
    """
    game_id: str
    active_player_id: Optional[str] = None
    turn_number: int = 0
    current_phase: TurnPhase = TurnPhase.DRAW
    status: GameStatus = GameStatus.WAITING
    winner_id: Optional[str] = None
    created_at: Optional[str] = None
    pending_action: Optional[str] = None
    pending_defender_id: Optional[str] = None
    pending_attack: Optional[dict[str, Any]] = None
    config: Optional["GameConfiguration"] = None
    total_cards: int = 0
    players: dict[str, PlayerState] = {}
    cards: dict[str, GameCard] = {}


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
    room: Annotated["GameRoom", SkipValidation] = Field(exclude=True)
    cards: dict[str, GameCard] = Field(default_factory=dict, exclude=True)
    active_player_id: Optional[str] = None
    turn_number: int = 0
    current_phase: TurnPhase = TurnPhase.DRAW
    status: GameStatus = GameStatus.WAITING
    winner_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    event_log: list[dict[str, Any]] = Field(default_factory=list, exclude=True)
    pending_action: Optional[str] = None
    pending_defender_id: Optional[str] = None
    pending_attack: Optional[dict[str, Any]] = None
    config: GameConfiguration = Field(default_factory=GameConfiguration)

    @computed_field
    @property
    def total_cards(self) -> float:
        return len(self.cards)
    
    @field_serializer('created_at')
    def serialize_created_at(self, value: datetime) -> str:
        return value.isoformat()
    
    @classmethod
    def create(cls, room: "GameRoom",
               config: Optional[GameConfiguration] = None) -> "GameState":
        """Factory method to create a new game."""
        instance = cls(
            game_id=str(uuid.uuid4()),
            room=room,
            config=config or GameConfiguration(),
        )
        room.state = instance
        return instance
    
    def get_card(self, instance_id: str) -> Optional[GameCard]:
        """Get a card by instance ID."""
        return self.cards.get(instance_id)
    
    def get_cards_in_zone(self, player_id: str, zone: Zone) -> list[GameCard]:
        """Get all cards in a specific zone for a player."""
        zone_state = self.room.players[player_id].zones[zone.name]
        return [self.cards[cid] for cid in zone_state.card_ids if cid in self.cards]
    
    def add_card(self, card: GameCard) -> None:
        """Add a card to the game."""
        self.cards[card.instance_id] = card
        player = self.room.players[card.owner_id]
        player.zones[card.zone.name].add_card(card.instance_id)
    
    def is_first_turn(self, player_id: str) -> bool:
        """Check if this is the first turn for a player."""
        return self.room.players[player_id].turn_count == 0
    
    def is_second_turn(self, player_id: str) -> bool:
        """Check if this is the second turn for a player."""
        return self.room.players[player_id].turn_count == 1
    
    def recalculate_elements(self, player_id: str) -> None:
        """Recalculate element pool for a player based on their active cards."""
        player = self.room.players[player_id]
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
        for player_id, player in self.room.players.items():
            total_cards = (
                len(player.zones[Zone.DECK.name].card_ids) +
                len(player.zones[Zone.HAND.name].card_ids) +
                len(player.get_active_cards())
            )
            if total_cards == 0:
                # Find opponent
                for pid, p in self.room.players.items():
                    if pid != player_id:
                        return p.player_id
        return None

    @staticmethod
    def _anonymized_card_payload(card: GameCard) -> dict[str, Any]:
        """Strip identity for hidden cards (any deck card, opponent hand)."""
        d = card.model_dump(mode="json")
        for key in d:
            if key in _VISIBLE_HIDDEN_FIELDS:
                continue
            if isinstance(d[key], list):
                d[key] = []
            elif isinstance(d[key], dict):
                d[key] = {}
            elif isinstance(d[key], bool):
                d[key] = False
            elif isinstance(d[key], (int, float)):
                d[key] = 0
            else:
                d[key] = None
        return d

    def serialize_for_player(self, player_id: str) -> dict[str, Any]:
        """Full game-state dict with per-player card visibility.

        Deck cards are always anonymized (for both players). Opponent hand
        cards are anonymized. Everything else is sent in full.
        """
        payload = self.model_dump(mode='json')

        payload["players"] = {
            pid: ps.model_dump(mode='json')
            for pid, ps in self.room.players.items()
        }

        cards_out: dict[str, dict[str, Any]] = {}
        for cid, card in self.cards.items():
            if card.zone == Zone.DECK:
                cards_out[cid] = self._anonymized_card_payload(card)
            elif card.owner_id != player_id and card.zone == Zone.HAND:
                cards_out[cid] = self._anonymized_card_payload(card)
            else:
                cards_out[cid] = card.model_dump(mode="json")

        payload["cards"] = cards_out

        return payload

    def _setup_deck(self, player: PlayerState) -> None:
        """Setup a player's deck from card data."""
        for card in player.deck:
            card = self._create_game_card(card, player.player_id)
            card.zone = Zone.DECK
            self.cards[card.instance_id] = card
            player.zones[Zone.DECK.name].add_card(card.instance_id)


    @staticmethod
    def _create_game_card(card_data: GameCardInput, owner_id: str) -> GameCard:
        """Create a GameCard from card data."""
        attacks = []
        for attack_data in card_data.attacks:
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

        element_contribution = list(card_data.element_contribution)

        # Default: contribute 1 of each element the card has
        if not element_contribution:
            for elem_id in card_data.element_ids:
                element_contribution.append(ElementContribution(element_id=elem_id, amount=1))

        return GameCard.create(
            card_id=card_data.id,
            owner_id=owner_id,
            name=card_data.name,
            health=card_data.health,
            physical_defence=card_data.physical_defence,
            magic_defence=card_data.magic_defence,
            element_ids=card_data.element_ids,
            element_contribution=element_contribution,
            attacks=attacks,
            skill_ids=card_data.skill_ids,
            association_ids=card_data.association_ids,
            evolves_from_id=card_data.evolves_from_id,
        )

__all__ = [
    "GameConfiguration",
    "GameState",
    "GameStateForPlayer",
]

