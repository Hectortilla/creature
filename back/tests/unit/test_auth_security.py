"""Pure JWT/password primitive tests (no DB/Redis) — lifts ``app.auth`` coverage.

Covers the security-critical behaviour of ``app.auth.security``: tokens
round-trip, wrong passwords are rejected, and expired/malformed/wrong-signature
tokens decode to ``None`` rather than slipping through.
"""

from __future__ import annotations

from datetime import timedelta

import jwt
import pytest

from app.auth.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)
from app.settings.config import get_settings

pytestmark = pytest.mark.unit

settings = get_settings()


def test_token_round_trip() -> None:
    payload = decode_access_token(create_access_token({"sub": "alice"}))
    assert payload["sub"] == "alice"
    assert "exp" in payload


def test_password_hash_round_trip() -> None:
    hashed = get_password_hash("secret")
    assert hashed != "secret"
    assert verify_password("secret", hashed)
    assert not verify_password("wrong", hashed)


def test_expired_token_is_rejected() -> None:
    expired = create_access_token({"sub": "alice"}, expires_delta=timedelta(seconds=-1))
    assert decode_access_token(expired) is None


def test_malformed_token_is_rejected() -> None:
    assert decode_access_token("not.a.jwt") is None


def test_wrong_signature_token_is_rejected() -> None:
    forged = jwt.encode({"sub": "alice"}, "a-different-secret", algorithm=settings.auth_algorithm)
    assert decode_access_token(forged) is None


def test_token_without_sub_decodes_without_sub() -> None:
    payload = decode_access_token(create_access_token({"role": "admin"}))
    assert "sub" not in payload
