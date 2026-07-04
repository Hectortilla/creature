"""Direct unit tests for the promotion / evolution / association action rules.

These action files carry no example tests (the ``no_tests`` mutation bucket), so
their validation, event, and enumeration logic can break silently. Each test
crafts a ``GameState`` with ``empty_state`` / ``place_card`` and drives the action
class directly: happy-path ``validate`` + ``to_events``, every rejection code, and
``get_valid`` enumeration. Pure engine, no DB. See ../../docs/harness.md.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest

from app.game.actions.association import AssociationAction
from app.game.actions.evolution import EvolutionAction
from app.game.actions.promotion import PromoteAction
from app.game.validators import RuleValidator
from app.models.game.card import EffectSpec, GameCard
from app.models.game.enums import GameStatus, TurnPhase, Zone
from app.models.game.events import CardAssociatedEvent, CardEvolvedEvent, CardPromotedEvent
from app.models.game.state import GameState

pytestmark = pytest.mark.unit

PlaceCard = Callable[..., GameCard]


def _in_hand(place_card: PlaceCard, state: GameState, owner_id: str, **fields: object) -> GameCard:
    card = place_card(state, owner_id, Zone.HAND, **fields)
    state.room.players[owner_id].zones[Zone.HAND.name].card_ids.append(card.instance_id)
    return card


def _past_first_turns(state: GameState, player_id: str = "p1") -> None:
    """Clear the first/second-turn restrictions that gate evolve/associate."""
    state.room.players[player_id].turn_count = 2


# ── Promotion ────────────────────────────────────────────────────────────


def test_promote_happy_path_and_event(empty_state: GameState, place_card: PlaceCard) -> None:
    card = place_card(empty_state, "p1", Zone.SUPPORTING, name="rookie", card_id=7, turns_in_zone=1)
    action = PromoteAction(player_id="p1", instance_id=card.instance_id)

    assert action.validate(empty_state).valid

    events = action.to_events(empty_state)
    assert len(events) == 1
    event = events[0]
    assert isinstance(event, CardPromotedEvent)
    assert event.instance_id == card.instance_id
    assert event.card_id == 7
    assert event.card_name == "rookie"


def test_promote_rejects_card_not_in_supporting(empty_state: GameState, place_card: PlaceCard) -> None:
    card = place_card(empty_state, "p1", Zone.ATTACKING, name="fighter", turns_in_zone=1)
    result = PromoteAction(player_id="p1", instance_id=card.instance_id).validate(empty_state)
    assert not result.valid
    assert result.error_code == "CARD_NOT_IN_SUPPORTING"


def test_promote_rejects_when_attacking_full(empty_state: GameState, place_card: PlaceCard) -> None:
    place_card(empty_state, "p1", Zone.ATTACKING, name="a1", turns_in_zone=1)
    place_card(empty_state, "p1", Zone.ATTACKING, name="a2", turns_in_zone=1)
    ready = place_card(empty_state, "p1", Zone.SUPPORTING, name="ready", turns_in_zone=1)

    result = PromoteAction(player_id="p1", instance_id=ready.instance_id).validate(empty_state)
    assert not result.valid
    assert result.error_code == "ATTACKING_ZONE_FULL"


def test_promote_rejects_card_not_ready(empty_state: GameState, place_card: PlaceCard) -> None:
    fresh = place_card(empty_state, "p1", Zone.SUPPORTING, name="fresh", turns_in_zone=0)
    result = PromoteAction(player_id="p1", instance_id=fresh.instance_id).validate(empty_state)
    assert not result.valid
    assert result.error_code == "CARD_NOT_READY"


def test_promote_get_valid_lists_only_ready_supporting_cards(empty_state: GameState, place_card: PlaceCard) -> None:
    ready = place_card(empty_state, "p1", Zone.SUPPORTING, name="ready", turns_in_zone=1)
    place_card(empty_state, "p1", Zone.SUPPORTING, name="fresh", turns_in_zone=0)

    actions = PromoteAction.get_valid(empty_state, "p1")
    assert [a.instance_id for a in actions] == [ready.instance_id]


def test_promote_get_valid_empty_when_attacking_full(empty_state: GameState, place_card: PlaceCard) -> None:
    place_card(empty_state, "p1", Zone.ATTACKING, name="a1", turns_in_zone=1)
    place_card(empty_state, "p1", Zone.ATTACKING, name="a2", turns_in_zone=1)
    place_card(empty_state, "p1", Zone.SUPPORTING, name="ready", turns_in_zone=1)

    assert PromoteAction.get_valid(empty_state, "p1") == []


def test_promote_wrong_phase_rejected_by_validator(empty_state: GameState, place_card: PlaceCard) -> None:
    card = place_card(empty_state, "p1", Zone.SUPPORTING, name="rookie", turns_in_zone=1)
    empty_state.status = GameStatus.IN_PROGRESS
    empty_state.active_player_id = "p1"
    empty_state.current_phase = TurnPhase.ATTACK

    result = RuleValidator().validate(empty_state, PromoteAction(player_id="p1", instance_id=card.instance_id))
    assert not result.valid
    assert result.error_code == "WRONG_PHASE"


# ── Evolution ──────────────────────────────────────────────────────────────


def _evolve_setup(empty_state: GameState, place_card: PlaceCard) -> tuple[GameCard, GameCard]:
    _past_first_turns(empty_state)
    base = place_card(empty_state, "p1", Zone.ATTACKING, name="base", card_id=42, turns_in_zone=1)
    evo = _in_hand(place_card, empty_state, "p1", name="super", card_id=99, evolves_from_id=42)
    return base, evo


def test_evolve_happy_path_and_event(empty_state: GameState, place_card: PlaceCard) -> None:
    base, evo = _evolve_setup(empty_state, place_card)
    action = EvolutionAction(player_id="p1", evolution_card_id=evo.instance_id, target_card_id=base.instance_id)

    assert action.validate(empty_state).valid

    events = action.to_events(empty_state)
    assert len(events) == 1
    event = events[0]
    assert isinstance(event, CardEvolvedEvent)
    assert event.base_card_id == base.instance_id
    assert event.evolution_card_id == evo.instance_id
    assert event.card_id == 99
    assert event.base_card_name == "base"
    assert event.evolution_card_name == "super"


def test_evolve_rejects_first_turn(empty_state: GameState, place_card: PlaceCard) -> None:
    base, evo = _evolve_setup(empty_state, place_card)
    empty_state.room.players["p1"].turn_count = 0
    result = EvolutionAction(
        player_id="p1", evolution_card_id=evo.instance_id, target_card_id=base.instance_id
    ).validate(empty_state)
    assert result.error_code == "FIRST_TURN_RESTRICTION"


def test_evolve_rejects_second_turn(empty_state: GameState, place_card: PlaceCard) -> None:
    base, evo = _evolve_setup(empty_state, place_card)
    empty_state.room.players["p1"].turn_count = 1
    result = EvolutionAction(
        player_id="p1", evolution_card_id=evo.instance_id, target_card_id=base.instance_id
    ).validate(empty_state)
    assert result.error_code == "SECOND_TURN_RESTRICTION"


def test_evolve_rejects_card_not_in_hand(empty_state: GameState, place_card: PlaceCard) -> None:
    _past_first_turns(empty_state)
    base = place_card(empty_state, "p1", Zone.ATTACKING, name="base", card_id=42, turns_in_zone=1)
    stray = place_card(empty_state, "p1", Zone.SUPPORTING, name="stray", card_id=99, evolves_from_id=42)
    result = EvolutionAction(
        player_id="p1", evolution_card_id=stray.instance_id, target_card_id=base.instance_id
    ).validate(empty_state)
    assert result.error_code == "CARD_NOT_IN_HAND"


def test_evolve_rejects_target_not_active(empty_state: GameState, place_card: PlaceCard) -> None:
    _past_first_turns(empty_state)
    stray_target = place_card(empty_state, "p1", Zone.HAND, name="base", card_id=42, turns_in_zone=1)
    evo = _in_hand(place_card, empty_state, "p1", name="super", card_id=99, evolves_from_id=42)
    result = EvolutionAction(
        player_id="p1", evolution_card_id=evo.instance_id, target_card_id=stray_target.instance_id
    ).validate(empty_state)
    assert result.error_code == "INVALID_TARGET"


def test_evolve_rejects_non_evolution_card(empty_state: GameState, place_card: PlaceCard) -> None:
    _past_first_turns(empty_state)
    base = place_card(empty_state, "p1", Zone.ATTACKING, name="base", card_id=42, turns_in_zone=1)
    plain = _in_hand(place_card, empty_state, "p1", name="plain", card_id=99)
    result = EvolutionAction(
        player_id="p1", evolution_card_id=plain.instance_id, target_card_id=base.instance_id
    ).validate(empty_state)
    assert result.error_code == "NOT_EVOLUTION_CARD"


def test_evolve_rejects_target_not_found(empty_state: GameState, place_card: PlaceCard) -> None:
    _past_first_turns(empty_state)
    empty_state.room.players["p1"].zones[Zone.ATTACKING.name].card_ids.append("ghost")
    evo = _in_hand(place_card, empty_state, "p1", name="super", card_id=99, evolves_from_id=42)
    result = EvolutionAction(player_id="p1", evolution_card_id=evo.instance_id, target_card_id="ghost").validate(
        empty_state
    )
    assert result.error_code == "TARGET_NOT_FOUND"


def test_evolve_rejects_mismatch(empty_state: GameState, place_card: PlaceCard) -> None:
    _past_first_turns(empty_state)
    base = place_card(empty_state, "p1", Zone.ATTACKING, name="base", card_id=13, turns_in_zone=1)
    evo = _in_hand(place_card, empty_state, "p1", name="super", card_id=99, evolves_from_id=42)
    result = EvolutionAction(
        player_id="p1", evolution_card_id=evo.instance_id, target_card_id=base.instance_id
    ).validate(empty_state)
    assert result.error_code == "EVOLUTION_MISMATCH"


def test_evolve_rejects_target_not_ready(empty_state: GameState, place_card: PlaceCard) -> None:
    _past_first_turns(empty_state)
    base = place_card(empty_state, "p1", Zone.ATTACKING, name="base", card_id=42, turns_in_zone=0)
    evo = _in_hand(place_card, empty_state, "p1", name="super", card_id=99, evolves_from_id=42)
    result = EvolutionAction(
        player_id="p1", evolution_card_id=evo.instance_id, target_card_id=base.instance_id
    ).validate(empty_state)
    assert result.error_code == "TARGET_NOT_READY"


def test_evolve_get_valid_pairs_matching_hand_evolutions(empty_state: GameState, place_card: PlaceCard) -> None:
    base, evo = _evolve_setup(empty_state, place_card)
    _in_hand(place_card, empty_state, "p1", name="unrelated", card_id=5, evolves_from_id=1000)

    actions = EvolutionAction.get_valid(empty_state, "p1")
    assert [(a.evolution_card_id, a.target_card_id) for a in actions] == [(evo.instance_id, base.instance_id)]


# ── Association ──────────────────────────────────────────────────────────────


def test_associate_happy_path_and_event(empty_state: GameState, place_card: PlaceCard) -> None:
    _past_first_turns(empty_state)
    target = place_card(empty_state, "p1", Zone.ATTACKING, name="host", turns_in_zone=1)
    assoc = place_card(empty_state, "p1", Zone.SUPPORTING, name="buff", card_id=55, association_ids=[700])
    action = AssociationAction(player_id="p1", association_card_id=assoc.instance_id, target_card_id=target.instance_id)

    assert action.validate(empty_state).valid

    events = action.to_events(empty_state)
    assert len(events) == 1
    event = events[0]
    assert isinstance(event, CardAssociatedEvent)
    assert event.association_card_id == assoc.instance_id
    assert event.target_card_id == target.instance_id
    assert event.card_id == 55
    assert event.source_zone == Zone.SUPPORTING
    assert event.swap_with_supporting_card_id == ""


def test_associate_rejects_first_turn(empty_state: GameState, place_card: PlaceCard) -> None:
    target = place_card(empty_state, "p1", Zone.ATTACKING, name="host", turns_in_zone=1)
    assoc = place_card(empty_state, "p1", Zone.SUPPORTING, name="buff", association_ids=[700])
    result = AssociationAction(
        player_id="p1", association_card_id=assoc.instance_id, target_card_id=target.instance_id
    ).validate(empty_state)
    assert result.error_code == "FIRST_TURN_RESTRICTION"


def test_associate_rejects_self_association(empty_state: GameState, place_card: PlaceCard) -> None:
    _past_first_turns(empty_state)
    assoc = place_card(empty_state, "p1", Zone.SUPPORTING, name="buff", association_ids=[700])
    result = AssociationAction(
        player_id="p1", association_card_id=assoc.instance_id, target_card_id=assoc.instance_id
    ).validate(empty_state)
    assert result.error_code == "SELF_ASSOCIATION"


def test_associate_rejects_invalid_source(empty_state: GameState, place_card: PlaceCard) -> None:
    _past_first_turns(empty_state)
    target = place_card(empty_state, "p1", Zone.ATTACKING, name="host", turns_in_zone=1)
    stray = place_card(empty_state, "p1", Zone.HAND, name="buff", association_ids=[700])
    result = AssociationAction(
        player_id="p1", association_card_id=stray.instance_id, target_card_id=target.instance_id
    ).validate(empty_state)
    assert result.error_code == "INVALID_ASSOCIATION_SOURCE"


def test_associate_rejects_invalid_target(empty_state: GameState, place_card: PlaceCard) -> None:
    _past_first_turns(empty_state)
    stray_target = place_card(empty_state, "p1", Zone.HAND, name="host", turns_in_zone=1)
    assoc = place_card(empty_state, "p1", Zone.SUPPORTING, name="buff", association_ids=[700])
    result = AssociationAction(
        player_id="p1", association_card_id=assoc.instance_id, target_card_id=stray_target.instance_id
    ).validate(empty_state)
    assert result.error_code == "INVALID_TARGET"


def test_associate_rejects_non_association_card(empty_state: GameState, place_card: PlaceCard) -> None:
    _past_first_turns(empty_state)
    target = place_card(empty_state, "p1", Zone.ATTACKING, name="host", turns_in_zone=1)
    plain = place_card(empty_state, "p1", Zone.SUPPORTING, name="plain")
    result = AssociationAction(
        player_id="p1", association_card_id=plain.instance_id, target_card_id=target.instance_id
    ).validate(empty_state)
    assert result.error_code == "NOT_ASSOCIATION_CARD"


def test_associate_rejects_when_limit_reached(empty_state: GameState, place_card: PlaceCard) -> None:
    _past_first_turns(empty_state)
    target = place_card(empty_state, "p1", Zone.ATTACKING, name="host", turns_in_zone=1)
    target.associations.append("already-linked")  # default limit is 1
    assoc = place_card(empty_state, "p1", Zone.SUPPORTING, name="buff", association_ids=[700])
    result = AssociationAction(
        player_id="p1", association_card_id=assoc.instance_id, target_card_id=target.instance_id
    ).validate(empty_state)
    assert result.error_code == "ASSOCIATION_LIMIT_REACHED"


def test_associate_rejects_when_forbidden(empty_state: GameState, place_card: PlaceCard) -> None:
    _past_first_turns(empty_state)
    target = place_card(
        empty_state,
        "p1",
        Zone.ATTACKING,
        name="loner",
        ability_ids=[903],
        turns_in_zone=1,
        specs=[
            EffectSpec(
                id=5,
                owner_kind="ability",
                owner_id=903,
                atom_type="rule-modifier",
                params={"scope": "self", "associations_allowed": False},
            ),
        ],
    )
    assoc = place_card(empty_state, "p1", Zone.SUPPORTING, name="buff", association_ids=[700])
    result = AssociationAction(
        player_id="p1", association_card_id=assoc.instance_id, target_card_id=target.instance_id
    ).validate(empty_state)
    assert result.error_code == "ASSOCIATIONS_FORBIDDEN"


def test_associate_rejects_swap_target_not_attacking(empty_state: GameState, place_card: PlaceCard) -> None:
    _past_first_turns(empty_state)
    target = place_card(empty_state, "p1", Zone.SUPPORTING, name="host", turns_in_zone=1)
    assoc = place_card(empty_state, "p1", Zone.SUPPORTING, name="buff", association_ids=[700])
    other = place_card(empty_state, "p1", Zone.SUPPORTING, name="bench")
    result = AssociationAction(
        player_id="p1",
        association_card_id=assoc.instance_id,
        target_card_id=target.instance_id,
        swap_with_supporting_card_id=other.instance_id,
    ).validate(empty_state)
    assert result.error_code == "INVALID_SWAP_ASSOCIATION_TARGET"


def test_associate_rejects_swap_card_not_in_supporting(empty_state: GameState, place_card: PlaceCard) -> None:
    _past_first_turns(empty_state)
    target = place_card(empty_state, "p1", Zone.ATTACKING, name="host", turns_in_zone=1)
    assoc = place_card(empty_state, "p1", Zone.SUPPORTING, name="buff", association_ids=[700])
    result = AssociationAction(
        player_id="p1",
        association_card_id=assoc.instance_id,
        target_card_id=target.instance_id,
        swap_with_supporting_card_id="not-a-real-card",
    ).validate(empty_state)
    assert result.error_code == "INVALID_SWAP_CARD"


def test_associate_get_valid_enumerates_source_target_pairs(empty_state: GameState, place_card: PlaceCard) -> None:
    _past_first_turns(empty_state)
    target = place_card(empty_state, "p1", Zone.ATTACKING, name="host", turns_in_zone=1)
    assoc = place_card(empty_state, "p1", Zone.SUPPORTING, name="buff", association_ids=[700])
    _in_hand(place_card, empty_state, "p1", name="plain")  # no association_ids → never a source

    actions = AssociationAction.get_valid(empty_state, "p1")
    assert [(a.association_card_id, a.target_card_id) for a in actions] == [(assoc.instance_id, target.instance_id)]
