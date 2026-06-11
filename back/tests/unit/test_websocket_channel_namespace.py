"""Pub/sub channels are namespaced by DB so stacks sharing one Redis don't cross-deliver.

Redis pub/sub is global across logical DBs, so isolating room/session state on
separate Redis DBs (dev /0, e2e /1, agent /2) does NOT isolate pub/sub. The
channel name must carry a per-stack namespace (the DB name) instead of the bare
player id, which collides across freshly-seeded DBs that both restart ids at 1.
"""

import pytest

from app.settings.config import Settings
from app.websocket import connections

pytestmark = pytest.mark.unit


def test_channel_namespace_is_database_name():
    settings = Settings(database_url="postgresql://postgres:postgres@localhost:5432/creature_e2e")
    assert settings.channel_namespace == "creature_e2e"


def test_distinct_databases_yield_distinct_namespaces():
    dev = Settings(database_url="postgresql://postgres:postgres@localhost:5432/creature")
    e2e = Settings(database_url="postgresql://postgres:postgres@localhost:5432/creature_e2e")
    assert dev.channel_namespace != e2e.channel_namespace


def test_player_channel_is_namespaced_not_bare_id():
    channel = connections._player_channel("1")
    assert channel != "1"
    assert connections.CHANNEL_PREFIX in channel
    assert channel.endswith(":player:1")
