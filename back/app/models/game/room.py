"""
Game Room

The room/lobby that owns the connected players and the live GameState. It is a
pure in-memory Pydantic model (no persistence), so it lives with the other
engine data types in app.models.game rather than in the websocket layer.
"""

from datetime import datetime

from pydantic import Field, computed_field, field_serializer

from app.models.game.base import GameBaseModel
from app.models.game.enums import GameStatus
from app.models.game.player import PlayerState
from app.models.game.state import GameState
from app.utils.time import utcnow


class RoomPlayerSummary(GameBaseModel):
    """A player as seen from the lobby: identity only, never their cards."""

    player_id: str
    name: str


class RoomSummary(GameBaseModel):
    """Public lobby view of a room: identity, flags, and player names — never hands, zones, or decks."""

    room_id: str
    host_id: str
    created_at: str
    players: list[RoomPlayerSummary]
    is_full: bool
    is_started: bool
    can_join: bool


class GameRoom(GameBaseModel):
    """
    Represents a game room/lobby.

    Uses Pydantic for automatic serialization via model_dump().
    """

    room_id: str
    host_id: str
    state: GameState | None = Field(default=None, exclude=True)
    players: dict[str, PlayerState] = Field(default_factory=dict)  # Player ID -> PlayerState
    created_at: datetime = Field(default_factory=utcnow)

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> str:
        return value.isoformat()

    @computed_field
    @property
    def is_full(self) -> bool:
        return len(self.players) == 2

    @computed_field
    @property
    def is_started(self) -> bool:
        return self.state is not None and self.state.status != GameStatus.WAITING

    @computed_field
    @property
    def can_join(self) -> bool:
        return not self.is_full and not self.is_started

    def to_summary(self) -> RoomSummary:
        """Public lobby summary: never exposes hands, zones, decks, or element pools."""
        return RoomSummary(
            room_id=self.room_id,
            host_id=self.host_id,
            created_at=self.created_at.isoformat(),
            players=[RoomPlayerSummary(player_id=p.player_id, name=p.name) for p in self.players.values()],
            is_full=self.is_full,
            is_started=self.is_started,
            can_join=self.can_join,
        )

    def get_player(self, player_id: str) -> PlayerState:
        """Get a player's state."""
        if player_id not in self.players:
            raise ValueError(f"Player {player_id} not found in room")
        return self.players[player_id]

    def get_active_player(self) -> PlayerState | None:
        """Get the active player's state."""
        if not self.state or not self.state.active_player_id:
            return None
        return self.players.get(self.state.active_player_id)

    def get_opponent(self, player_id: str) -> PlayerState:
        """Get the opponent of a given player."""
        for pid, player in self.players.items():
            if pid != player_id:
                return player
        raise ValueError(f"No opponent found for player {player_id}")

    def add_player(self, player: "PlayerState") -> None:
        """Add a player to the room."""
        if player.deck is None:
            raise ValueError("Player deck is required")

        if len(self.players) == 2:
            raise ValueError("Room is full")

        self.players[player.player_id] = player

    def remove_player(self, player_id: str) -> None:
        """Remove a player from the room."""
        if player_id not in self.players:
            raise ValueError(f"Player {player_id} not found in room")
        del self.players[player_id]

    def get_player_ids(self) -> list[str]:
        """Get list of player IDs in the room."""
        return list(self.players.keys())

    def game_ready_to_start(self) -> bool:
        """Check if the game is ready to start."""
        if self.state:
            return False
        return len(self.players.keys()) >= 2


# GameState holds a forward reference to GameRoom (a TYPE_CHECKING-only import in
# state.py, to avoid the runtime cycle). Now that GameRoom is defined, rebuild
# GameState so that annotation resolves. GameRoom is in this module's namespace,
# which is what model_rebuild() uses to resolve the reference.
GameState.model_rebuild()
