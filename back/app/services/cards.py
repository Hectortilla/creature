from sqlmodel import select, or_

from app.models.db.card import Card
from app.models.db.attack import Attack
from app.models.db.ability import Ability
from app.models.db.association import Association
from app.models.schemas.card import CardCreate, CardRead, CardReadWithRelations
from app.models.schemas.element import ElementRead
from app.models.schemas.type import TypeRead
from app.models.schemas.character import CharacterRead
from app.models.schemas.attack import AttackReadWithElement
from app.models.schemas.ability import AbilityRead
from app.models.schemas.association import AssociationRead
from app.services.base import BaseService


class CardService(BaseService[Card, CardCreate]):
    """Service for Card CRUD operations with enrichment."""
    
    model = Card
    lookup_id_field = "code"
    lookup_str_field = "name"
    has_handle = True
    
    def _get_strengths(self, first_element, second_element) -> list[int] | None:
        """Calculate card strengths based on both elements."""
        strengths = set()
        if first_element and first_element.strengths:
            strengths.update(first_element.strengths)
        if second_element and second_element.strengths:
            strengths.update(second_element.strengths)
        return list(strengths) if strengths else None
    
    def _get_weaknesses(self, first_element, second_element) -> list[int] | None:
        """Calculate card weaknesses based on both elements."""
        weaknesses = set()
        if first_element and first_element.weaknesses:
            weaknesses.update(first_element.weaknesses)
        if second_element and second_element.weaknesses:
            weaknesses.update(second_element.weaknesses)
        return list(weaknesses) if weaknesses else None
    
    def _enrich_attack(self, attack) -> AttackReadWithElement | None:
        """Convert attack to AttackReadWithElement."""
        if not attack:
            return None
        
        element_read = ElementRead.model_validate(attack.element) if attack.element else None
        
        return AttackReadWithElement(
            id=attack.id,
            created_at=attack.created_at,
            code=attack.code,
            name=attack.name,
            handle=attack.handle,
            description=attack.description,
            damage=attack.damage,
            type=attack.type,
            element_id=attack.element_id,
            element=element_read,
            dice_rolls=attack.dice_rolls,
            necessary_force=attack.necessary_force,
            effect=attack.effect,
            strengths=attack.element.strengths if attack.element else None,
            weaknesses=attack.element.weaknesses if attack.element else None,
        )
    
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
            first_attack=self._enrich_attack(card.first_attack),
            second_attack=self._enrich_attack(card.second_attack),
            ability=AbilityRead.model_validate(card.ability) if card.ability else None,
            association=AssociationRead.model_validate(card.association) if card.association else None,
            is_evolution=is_evolution_read,
            next_evolutions=next_evolutions_read,
            strengths=self._get_strengths(card.first_element, card.second_element),
            weaknesses=self._get_weaknesses(card.first_element, card.second_element),
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
