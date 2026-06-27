"""Pure (DB-free) service helpers — marked ``unit`` so they lift ``make check``:
``format_handle`` slugification and ``serialize_deck_for_game`` on an empty deck.
"""

from __future__ import annotations

import pytest

from app.services.base import format_handle
from app.services.player_state import serialize_deck_for_game

pytestmark = pytest.mark.unit


def test_serialize_empty_deck_is_empty() -> None:
    assert serialize_deck_for_game([]) == []


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("  Fire & Ice!  ", "fire-ice"),
        ("Hello World", "hello-world"),
        ("multi___under", "multi-under"),
    ],
)
def test_format_handle_slugifies(name: str, expected: str) -> None:
    assert format_handle(name) == expected
