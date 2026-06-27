"""BaseService CRUD via a concrete subclass (``ElementService``): create, get by
id and by string label (the ``ilike`` branch), get_all, and delete returning
True/False. Covers the generic machinery every simple service inherits. Needs
Postgres.
"""

from __future__ import annotations

import pytest
from sqlmodel import Session

from app.models.schemas.element import ElementCreate
from app.services.base import ElementService

pytestmark = pytest.mark.integration


def test_element_crud_roundtrip(session: Session) -> None:
    svc = ElementService(session)
    created = svc.create(ElementCreate(label="Wind"))

    assert created.id is not None
    assert svc.get(created.id).label == "Wind"
    assert svc.get("Wind").id == created.id  # string lookup via ilike
    assert any(e.id == created.id for e in svc.get_all())

    assert svc.delete(created.id) is True
    assert svc.get(created.id) is None
    assert svc.delete(created.id) is False
