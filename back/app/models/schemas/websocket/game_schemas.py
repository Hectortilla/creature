"""
Game-specific WebSocket Schemas

Types that extend existing models for the server→client response shape.
Only contains schemas that can't directly reuse a game model.
"""

from typing import Optional

from app.models.schemas.websocket.client import ActionData


class ValidActionSchema(ActionData):
    """Action.to_dict() output = ActionData fields + server enrichments."""
    player_id: str
    action: str
    description: Optional[str] = None
    card_name: Optional[str] = None
    attack_name: Optional[str] = None
    target_name: Optional[str] = None
    attacker_name: Optional[str] = None
    supporting_card_name: Optional[str] = None
    attacking_card_name: Optional[str] = None
    association_card_name: Optional[str] = None
    target_card_name: Optional[str] = None
    evolution_card_name: Optional[str] = None
    cards: Optional[list[dict]] = None
