"""
Game State Models

Core game state models including configuration and full game state.
"""

from __future__ import annotations

import random
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Annotated, Any

from pydantic import Field, PrivateAttr, SkipValidation, computed_field, field_serializer

from app.models.game.attack import AttackDefinition, PendingAttack
from app.models.game.base import GameBaseModel
from app.models.game.card import GameCard, GameCardInput
from app.models.game.element import ElementContribution
from app.models.game.enums import DamageType, GameStatus, TurnPhase, Zone
from app.models.game.player import PlayerState
from app.utils.time import utcnow

if TYPE_CHECKING:
    from app.models.game.room import GameRoom

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
    active_player_id: str | None = None
    turn_number: int = 0
    current_phase: TurnPhase = TurnPhase.DRAW
    status: GameStatus = GameStatus.WAITING
    winner_id: str | None = None
    created_at: str | None = None
    pending_action: str | None = None
    pending_defender_id: str | None = None
    pending_attack: PendingAttack | None = None
    pending_forced_swap_target_id: str | None = None
    pending_forced_swap_source_id: str | None = None
    config: GameConfiguration | None = None
    total_cards: int = 0
    players: dict[str, dict[str, Any]] = {}
    cards: dict[str, dict[str, Any]] = {}


class GameConfiguration(GameBaseModel):
    """
    Configuration options for a game.
    """

    deck_size: int = 22
    initial_draw: int = 4
    normal_draw: int = 1
    supporting_zone_size: int = 3
    attacking_zone_size: int = 2
    seed: int | None = None


class GameState(GameBaseModel):
    """
    Complete state of a game.
    """

    game_id: str
    room: Annotated[GameRoom, SkipValidation] = Field(exclude=True)
    cards: dict[str, GameCard] = Field(default_factory=dict, exclude=True)
    active_player_id: str | None = None
    turn_number: int = 0
    current_phase: TurnPhase = TurnPhase.DRAW
    status: GameStatus = GameStatus.WAITING
    winner_id: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    pending_action: str | None = None
    pending_defender_id: str | None = None
    pending_attack: PendingAttack | None = None
    pending_forced_swap_target_id: str | None = None
    pending_forced_swap_source_id: str | None = None
    config: GameConfiguration = Field(default_factory=GameConfiguration)

    # Per-game RNG seeded from ``config.seed`` for deterministic shuffles/deal.
    # ``PrivateAttr`` so it never leaks into ``model_dump``/``serialize_for_player``.
    _rng: random.Random = PrivateAttr(default_factory=random.Random)

    @property
    def rng(self) -> random.Random:
        """The per-game random source for shuffles, first-player, and dice."""
        return self._rng

    @computed_field
    @property
    def total_cards(self) -> float:
        return len(self.cards)

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> str:
        return value.isoformat()

    @classmethod
    def create(cls, room: GameRoom, config: GameConfiguration | None = None) -> GameState:
        """Factory method to create a new game."""
        instance = cls(
            game_id=str(uuid.uuid4()),
            room=room,
            config=config or GameConfiguration(),
        )
        instance._rng = random.Random(instance.config.seed)
        room.state = instance
        return instance

    def get_card(self, instance_id: str) -> GameCard | None:
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
        active_cards = [self.cards[cid] for cid in player.get_active_cards() if cid in self.cards]
        player.element_pool.recalculate_from_cards(active_cards)

    def check_game_end(self) -> str | None:
        """
        Check if the game has ended.
        Returns the winner's player_id if game is over, None otherwise.
        """
        for player_id, player in self.room.players.items():
            total_cards = (
                len(player.zones[Zone.DECK.name].card_ids)
                + len(player.zones[Zone.HAND.name].card_ids)
                + len(player.get_active_cards())
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

    def serialize_for_player(self, player_id: str) -> GameStateForPlayer:
        """Full game-state payload with per-player card visibility.

        Deck cards are always anonymized (for both players). Opponent hand
        cards are anonymized. Everything else is sent in full.
        """
        payload = self.model_dump(mode="json")

        payload["players"] = {pid: ps.model_dump(mode="json") for pid, ps in self.room.players.items()}

        cards_out: dict[str, dict[str, Any]] = {}
        for cid, card in self.cards.items():
            if card.zone == Zone.DECK or (card.owner_id != player_id and card.zone == Zone.HAND):
                cards_out[cid] = self._anonymized_card_payload(card)
            else:
                cards_out[cid] = card.model_dump(mode="json")

        payload["cards"] = cards_out

        return GameStateForPlayer.model_validate(payload)

    def _setup_deck(self, player: PlayerState) -> None:
        """Setup a player's deck from card data."""
        for card_input in player.deck or []:
            card = self._create_game_card(card_input, player.player_id)
            card.zone = Zone.DECK
            self.cards[card.instance_id] = card
            player.zones[Zone.DECK.name].add_card(card.instance_id)

    @staticmethod
    def _create_game_card(card_data: GameCardInput, owner_id: str) -> GameCard:
        """Create a GameCard from card data."""
        # Imported lazily: app.game.effects imports app.models.game, so importing
        # it at module load would create a circular import through this package.
        from app.game.effects import build_effect_atoms

        attacks = []
        for attack_data in card_data.attacks:
            attack_type = DamageType.PHYSICAL
            if attack_data.type.lower() == "magical":
                attack_type = DamageType.MAGICAL

            attacks.append(
                AttackDefinition(
                    attack_id=attack_data.id,
                    name=attack_data.name,
                    damage=attack_data.damage,
                    type=attack_type,
                    element_id=attack_data.element_id,
                    necessary_force=list(attack_data.necessary_force),
                    effect=attack_data.effect,
                    description=attack_data.description,
                    dice_rolls=attack_data.dice_rolls,
                )
            )

        element_contribution = list(card_data.element_contribution)

        # Default: contribute 1 of each element the card has
        if not element_contribution:
            for elem_id in card_data.element_ids:
                element_contribution.append(ElementContribution(element_id=elem_id, amount=1))

        game_card = GameCard.create(
            card_id=card_data.id,
            owner_id=owner_id,
            name=card_data.name,
            health=card_data.health,
            physical_defence=card_data.physical_defence,
            magic_defence=card_data.magic_defence,
            element_ids=card_data.element_ids,
            element_contribution=element_contribution,
            type_id=card_data.type_id,
            character_id=card_data.character_id,
            character_name=card_data.character_name,
            attacks=attacks,
            ability_ids=card_data.ability_ids,
            association_ids=card_data.association_ids,
            effect_specs=card_data.effect_specs,
            evolves_from_id=card_data.evolves_from_id,
            effect_atoms=build_effect_atoms(card_data.effect_specs),
        )
        return game_card


__all__ = [
    "GameConfiguration",
    "GameState",
    "GameStateForPlayer",
]
