"""
Element Models

Models for element contributions and element pools.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.models.game.base import GameBaseModel
from app.models.game.enums import Zone

if TYPE_CHECKING:
    from app.models.game.card import GameCard


class ElementContribution(GameBaseModel):
    """
    Represents element contribution from a card.
    Used for element costs, contributions, and any element+amount pair.
    """
    element_id: int
    amount: int


class ElementPool(GameBaseModel):
    """
    Tracks available elements for a player.
    """
    elements: dict[int, int] = {}
    max_elements: dict[int, int] = {}
    
    def get_available(self, element_id: int) -> int:
        """Get available amount of an element."""
        return self.elements.get(element_id, 0)
    
    def consume(self, element_id: int, amount: int) -> bool:
        """Consume elements. Returns False if not enough available."""
        available = self.get_available(element_id)
        if available < amount:
            return False
        self.elements[element_id] = available - amount
        return True
    
    def consume_multiple(self, costs: list[ElementContribution]) -> bool:
        """
        Consume multiple element costs. 
        All-or-nothing - either all costs are paid or none are.
        """
        for cost in costs:
            if self.get_available(cost.element_id) < cost.amount:
                return False
        for cost in costs:
            self.consume(cost.element_id, cost.amount)
        return True
    
    def add(self, element_id: int, amount: int) -> None:
        """Add elements to the pool."""
        current = self.elements.get(element_id, 0)
        self.elements[element_id] = current + amount
        max_current = self.max_elements.get(element_id, 0)
        self.max_elements[element_id] = max(max_current, current + amount)
    
    def restore(self) -> None:
        """Restore elements to their maximum values."""
        self.elements = self.max_elements.copy()
    
    def recalculate_from_cards(self, cards: list["GameCard"]) -> None:
        """Recalculate element pool from contributing cards."""
        self.elements.clear()
        self.max_elements.clear()
        
        for card in cards:
            if card.zone in (Zone.SUPPORTING, Zone.ATTACKING):
                for contrib in card.get_element_contribution():
                    current = self.elements.get(contrib.element_id, 0)
                    self.elements[contrib.element_id] = current + contrib.amount
        
        self.max_elements = self.elements.copy()


__all__ = [
    "ElementContribution",
    "ElementPool",
]

