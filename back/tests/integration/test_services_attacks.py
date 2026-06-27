"""AttackService enrichment tests: ``enrich`` lifts the element's strengths/
weaknesses onto the read model, and ``get_enriched`` returns ``None`` for an
unknown code (the negative path enrichment callers rely on). Needs Postgres.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest
from sqlmodel import Session

from app.models.db.attack import Attack
from app.models.db.element import Element
from app.services.attacks import AttackService

pytestmark = pytest.mark.integration


@pytest.fixture
def codes() -> Callable[[], int]:
    counter = iter(range(9_000_001, 9_010_000))
    return lambda: next(counter)


def test_enrich_lifts_element_strengths(session: Session, codes: Callable[[], int]) -> None:
    elem = Element(label="Spark", strengths=[7], weaknesses=[8])
    session.add(elem)
    session.flush()
    attack = Attack(code=codes(), name="Jolt", element_id=elem.id)
    session.add(attack)
    session.flush()

    read = AttackService(session).enrich(attack)
    assert read.name == "Jolt"
    assert read.element.label == "Spark"
    assert read.strengths == [7]
    assert read.weaknesses == [8]


def test_enrich_without_element_has_no_strengths(session: Session, codes: Callable[[], int]) -> None:
    attack = Attack(code=codes(), name="Plain")
    session.add(attack)
    session.flush()

    read = AttackService(session).enrich(attack)
    assert read.element is None
    assert read.strengths is None


def test_get_enriched_unknown_returns_none(session: Session) -> None:
    assert AttackService(session).get_enriched(8_888_888) is None
