"""
Card Service

CRUD operations for cards with enrichment logic.
"""

from sqlmodel import select, or_

from app.models.db.card import Card
from app.models.db.attack import Attack
from app.models.db.ability import Ability
from app.models.db.association import Association
from app.models.db.effect import Effect
from app.models.schemas.card import CardCreate, CardRead, CardReadWithRelations
from app.models.schemas.element import ElementRead
from app.models.schemas.type import TypeRead
from app.models.schemas.character import CharacterRead
from app.models.schemas.ability import AbilityRead
from app.models.schemas.association import AssociationRead
from app.models.schemas.effect import EffectRead
from app.services.attacks import enrich_attack
from app.services.base import BaseService


class CardService(BaseService[Card, CardCreate]):
    """Service for Card CRUD operations with enrichment."""
    
    model = Card
    lookup_id_field = "code"
    lookup_str_field = "name"
    has_handle = True
    
    @staticmethod
    def _aggregate_element_property(first_element, second_element, prop: str) -> list[int] | None:
        """Aggregate an element property (strengths/weaknesses) from both elements."""
        values = set()
        for elem in (first_element, second_element):
            if elem and (attr_val := getattr(elem, prop, None)):
                values.update(attr_val)
        return list(values) if values else None
    
    def _to_card_read(self, card: Card) -> CardRead:
        """Convert Card to CardRead schema."""
        return CardRead(
            id=card.id,
            created_at=card.created_at,
            code=card.code,
            name=card.name,
            handle=card.handle,
            description=card.description,
            image=card.image,
            overlay_image=card.overlay_image,
            health=card.health,
            physical_defence=card.physical_defence,
            magic_defence=card.magic_defence,
            forces=card.forces,
            is_evolution_id=card.is_evolution_id,
            first_element_id=card.first_element_id,
            second_element_id=card.second_element_id,
            type_id=card.type_id,
            character_id=card.character_id,
            first_attack_id=card.first_attack_id,
            second_attack_id=card.second_attack_id,
            ability_id=card.ability_id,
            association_id=card.association_id,
        )

    def _get_effects_for_card(self, card: Card) -> list[EffectRead]:
        """Fetch enabled effect rows for this card's ability, attacks, and association."""
        owner_filters = []
        if card.ability_id:
            owner_filters.append((Effect.owner_kind == "ability") & (Effect.owner_id == card.ability_id))
        if card.first_attack_id:
            owner_filters.append((Effect.owner_kind == "attack") & (Effect.owner_id == card.first_attack_id))
        if card.second_attack_id:
            owner_filters.append((Effect.owner_kind == "attack") & (Effect.owner_id == card.second_attack_id))
        if card.association_id:
            owner_filters.append((Effect.owner_kind == "association") & (Effect.owner_id == card.association_id))
        if not owner_filters:
            return []

        rows = self.db.exec(
            select(Effect)
            .where(Effect.enabled == True)  # noqa: E712
            .where(or_(*owner_filters))
            .order_by(Effect.owner_kind, Effect.owner_id, Effect.sort_order, Effect.id)
        ).all()
        return [EffectRead.model_validate(row) for row in rows]
    
    def enrich(self, card: Card, visited: set | None = None) -> CardReadWithRelations:
        """Enrich card with all relationships and computed properties."""
        if visited is None:
            visited = set()
        
        # Return minimal response for circular references
        if card.code in visited:
            return self._to_card_read(card)
        
        visited.add(card.code)
        
        # Get next evolutions
        next_evos = self.db.exec(
            select(Card).where(Card.is_evolution_id == card.id)
        ).all()
        
        next_evolutions_read = [self._to_card_read(evo) for evo in next_evos] if next_evos else None
        is_evolution_read = self._to_card_read(card.is_evolution) if card.is_evolution else None
        
        return CardReadWithRelations(
            id=card.id,
            created_at=card.created_at,
            code=card.code,
            name=card.name,
            handle=card.handle,
            description=card.description,
            image=card.image,
            overlay_image=card.overlay_image,
            health=card.health,
            physical_defence=card.physical_defence,
            magic_defence=card.magic_defence,
            forces=card.forces,
            is_evolution_id=card.is_evolution_id,
            first_element_id=card.first_element_id,
            second_element_id=card.second_element_id,
            type_id=card.type_id,
            character_id=card.character_id,
            first_attack_id=card.first_attack_id,
            second_attack_id=card.second_attack_id,
            ability_id=card.ability_id,
            association_id=card.association_id,
            first_element=ElementRead.model_validate(card.first_element) if card.first_element else None,
            second_element=ElementRead.model_validate(card.second_element) if card.second_element else None,
            type=TypeRead.model_validate(card.type) if card.type else None,
            character=CharacterRead.model_validate(card.character) if card.character else None,
            first_attack=enrich_attack(card.first_attack),
            second_attack=enrich_attack(card.second_attack),
            ability=AbilityRead.model_validate(card.ability) if card.ability else None,
            association=AssociationRead.model_validate(card.association) if card.association else None,
            is_evolution=is_evolution_read,
            next_evolutions=next_evolutions_read,
            strengths=self._aggregate_element_property(card.first_element, card.second_element, "strengths"),
            weaknesses=self._aggregate_element_property(card.first_element, card.second_element, "weaknesses"),
            effects=self._get_effects_for_card(card),
        )
    
    def get_all_enriched(self) -> list[CardReadWithRelations]:
        """Get all cards with enriched data."""
        cards = self.get_all()
        return [self.enrich(card) for card in cards]
    
    def get_enriched(self, value: int | str) -> list[CardReadWithRelations]:
        """Get card by code, handle, or name with enriched data."""
        if isinstance(value, int) or (isinstance(value, str) and value.isdigit()):
            cards = self.db.exec(
                select(Card).where(Card.code == int(value))
            ).all()
        else:
            cards = self.db.exec(
                select(Card).where(
                    or_(
                        Card.handle.ilike(value),
                        Card.name.ilike(value)
                    )
                )
            ).all()
        
        return [self.enrich(card) for card in cards]
    
    def get_by_attack(self, attack_code: int) -> list[CardReadWithRelations]:
        """Get all cards that have a specific attack."""
        cards = self.db.exec(
            select(Card).where(
                or_(
                    Card.first_attack.has(Attack.code == attack_code),
                    Card.second_attack.has(Attack.code == attack_code)
                )
            )
        ).all()
        return [self.enrich(card) for card in cards]
    
    def get_by_ability(self, ability_code: int) -> list[CardReadWithRelations]:
        """Get all cards that have a specific ability."""
        cards = self.db.exec(
            select(Card).where(Card.ability.has(Ability.code == ability_code))
        ).all()
        return [self.enrich(card) for card in cards]
    
    def get_by_association(self, association_code: int) -> list[CardReadWithRelations]:
        """Get all cards that have a specific association."""
        cards = self.db.exec(
            select(Card).where(Card.association.has(Association.code == association_code))
        ).all()
        return [self.enrich(card) for card in cards]
