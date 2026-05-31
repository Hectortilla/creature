"""Exemplar integration test: the database accepts a trivial query.

Demonstrates the ``integration`` marker plus the ``db_session`` fixture from
``conftest.py``. Excluded from the default ``make test``; runs in CI's
integration job against a Postgres service. Real DB tests (CRUD via
``app.services``, or routes via ``TestClient``) follow this shape.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlmodel import Session

pytestmark = pytest.mark.integration


def test_database_accepts_trivial_query(db_session: Session) -> None:
    value = db_session.connection().execute(text("SELECT 1")).scalar_one()
    assert value == 1
