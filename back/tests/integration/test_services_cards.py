"""CardService enrichment tests: ``enrich`` aggregates element strengths from both
elements, attaches the attack read model, and ``get_enriched`` resolves by code.

Enrichment is the read-model contract the frontend depends on; a broken join or
aggregate would ship a silently wrong card. Needs Postgres.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest
from sqlmodel import Session

from app.models.db.attack import Attack
from app.models.db.card import Card
from app.models.db.element import Element
from app.services.cards import CardService

pytestmark = pytest.mark.integration


@pytest.fixture
def codes() -> Callable[[], int]:
    counter = iter(range(9_000_001, 9_010_000))
    return lambda: next(counter)


def test_enrich_aggregates_elements_and_attaches_attack(session: Session, codes: Callable[[], int]) -> None:
    fire = Element(label="Fire", strengths=[1, 2], weaknesses=[3])
    water = Element(label="Water", strengths=[2, 4])
    session.add_all([fire, water])
    session.flush()
    attack = Attack(code=codes(), name="Ember", element_id=fire.id)
    session.add(attack)
    session.flush()
    card = Card(
        code=codes(),
        name="Charcat",
        first_element_id=fire.id,
        second_element_id=water.id,
        first_attack_id=attack.id,
    )
    session.add(card)
    session.flush()

    read = CardService(session).enrich(card)
    assert read.name == "Charcat"
    assert set(read.strengths) == {1, 2, 4}
    assert read.first_attack.name == "Ember"


def test_get_enriched_by_code_returns_match(session: Session, codes: Callable[[], int]) -> None:
    card = Card(code=codes(), name="Solo")
    session.add(card)
    session.flush()

    results = CardService(session).get_enriched(card.code)
    assert [c.code for c in results] == [card.code]


def test_get_enriched_unknown_returns_empty(session: Session) -> None:
    assert CardService(session).get_enriched(8_888_888) == []
