"""
Game-specific WebSocket Schemas

Types that extend existing models for the server→client response shape.
Only contains schemas that can't directly reuse a game model.
"""

from app.models.schemas.websocket.client import ActionData


class ValidActionSchema(ActionData):
    """Action.to_dict() output = ActionData fields + server enrichments."""

    player_id: str
    action: str
    description: str | None = None
    card_name: str | None = None
    attack_name: str | None = None
    target_name: str | None = None
    attacker_name: str | None = None
    supporting_card_name: str | None = None
    attacking_card_name: str | None = None
    association_card_name: str | None = None
    target_card_name: str | None = None
    evolution_card_name: str | None = None
    cards: list[dict] | None = None
