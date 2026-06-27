"""UserService tests: password is hashed on create, lookups, and authenticate
accepting the right password while rejecting wrong password / unknown user.

The hashing + reject paths are the security-sensitive surface (a regression that
stores plaintext or accepts a bad password would pass a happy-path-only test).
Needs Postgres (services take a live ``Session``).
"""

from __future__ import annotations

import pytest
from sqlmodel import Session

from app.auth.security import verify_password
from app.models.schemas.user import UserCreate
from app.services.users import UserService

pytestmark = pytest.mark.integration


def test_create_hashes_password(session: Session) -> None:
    user = UserService(session).create(UserCreate(username="alice", password="secret", email="a@b.c"))

    assert user.hashed_password != "secret"
    assert verify_password("secret", user.hashed_password)


def test_lookups_find_the_created_user(session: Session) -> None:
    svc = UserService(session)
    user = svc.create(UserCreate(username="bob", password="pw", email="bob@x.y"))

    assert svc.get_by_username("bob").id == user.id
    assert svc.get_by_email("bob@x.y").id == user.id
    assert svc.get_by_id(user.id).username == "bob"
    assert svc.get_by_username("nobody") is None


def test_authenticate_accepts_right_rejects_wrong(session: Session) -> None:
    svc = UserService(session)
    svc.create(UserCreate(username="carol", password="pw"))

    assert svc.authenticate("carol", "pw") is not None
    assert svc.authenticate("carol", "wrong") is None
    assert svc.authenticate("nobody", "pw") is None
