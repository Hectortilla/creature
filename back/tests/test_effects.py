"""
Focused unit tests for the data-driven effect engine (app.game.effects).

These build a tiny GameState by hand and assert the passive-query results for
representative atoms: stat auras, defense override, immunity, association
limits, and incoming-damage modifiers. No database required.

Runnable directly:

    .venv/bin/python -m tests.test_effects
"""

from __future__ import annotations

from app.models.game.attack import AttackDefinition
from app.models.game.card import EffectSpec, GameCard
from app.models.game.enums import CardStatus, DamageType, Zone
from app.models.game.player import PlayerState
from app.models.game.state import GameState
from app.websocket.models import GameRoom
from app.game import effects
from app.game.effects import PassiveCategory, build_effect_atoms


def _empty_state() -> GameState:
    room = GameRoom(room_id="r", host_id="p1")
    room.add_player(PlayerState(player_id="p1", name="P1", deck=[]))
    room.add_player(PlayerState(player_id="p2", name="P2", deck=[]))
    return GameState.create(room)


def _place(state: GameState, owner_id: str, zone: Zone, specs: list[EffectSpec] | None = None, **fields) -> GameCard:
    card = GameCard.create(
        card_id=fields.pop("card_id", 1),
        owner_id=owner_id,
        name=fields.pop("name", "card"),
        health=fields.pop("health", 50),
        physical_defence=fields.pop("physical_defence", 5),
        magic_defence=fields.pop("magic_defence", 5),
        effect_atoms=build_effect_atoms(specs or []),
        **fields,
    )
    card.zone = zone
    state.cards[card.instance_id] = card
    if zone in (Zone.SUPPORTING, Zone.ATTACKING):
        state.room.players[owner_id].zones[zone.name].card_ids.append(card.instance_id)
    return card


def _attack(element_id: int = 5, type_: DamageType = DamageType.PHYSICAL) -> AttackDefinition:
    return AttackDefinition(attack_id=1, name="a", damage=20, type=type_, element_id=element_id)


def test_stat_aura_targets_active_allies_only() -> None:
    state = _empty_state()
    _place(state, "p1", Zone.ATTACKING, name="aura", ability_ids=[900], specs=[
        EffectSpec(id=1, owner_kind="ability", owner_id=900, atom_type="stat-modifier",
                     params={"scope": "allies_active", "attack": 10}),
    ])
    ally = _place(state, "p1", Zone.ATTACKING, name="ally")
    enemy = _place(state, "p2", Zone.ATTACKING, name="enemy")

    assert effects.get_passive_stat_modifiers(state, ally)["attack_bonus"] == 10
    assert effects.get_passive_stat_modifiers(state, enemy)["attack_bonus"] == 0


def test_defense_override_wins_over_additive_defense() -> None:
    state = _empty_state()
    host = _place(state, "p1", Zone.ATTACKING, name="host")
    assoc = _place(state, "p1", Zone.SUPPORTING, name="curse", association_ids=[700], specs=[
        EffectSpec(id=2, owner_kind="association", owner_id=700, atom_type="stat-modifier",
                     params={"scope": "host", "defense_override": 0, "attack": 40}),
    ])
    assoc.status = CardStatus.ASSOCIATED
    assoc.association_target_id = host.instance_id
    host.associations.append(assoc.instance_id)

    mods = effects.get_passive_stat_modifiers(state, host, attack=_attack())
    assert mods["attack_bonus"] == 40
    assert mods["defense_bonus"] == 0  # override applied, not the (absent) additive value


def test_immunity_respects_enemy_damage_type() -> None:
    state = _empty_state()
    card = _place(state, "p1", Zone.ATTACKING, name="ghost", ability_ids=[901], specs=[
        EffectSpec(id=3, owner_kind="ability", owner_id=901, atom_type="immunity",
                     params={"scope": "self", "enemy_damage_type": "physical"}),
    ])
    attacker = _place(state, "p2", Zone.ATTACKING, name="atk")

    assert effects.is_immune_to_attack(state, card, _attack(type_=DamageType.PHYSICAL), attacker) is True
    assert effects.is_immune_to_attack(state, card, _attack(type_=DamageType.MAGICAL), attacker) is False


def test_association_limit_and_forbidden() -> None:
    state = _empty_state()
    teamwork = _place(state, "p1", Zone.ATTACKING, name="team", ability_ids=[902], specs=[
        EffectSpec(id=4, owner_kind="ability", owner_id=902, atom_type="rule-modifier",
                     params={"scope": "self", "max_associations": 2}),
    ])
    loner = _place(state, "p1", Zone.ATTACKING, name="loner", ability_ids=[903], specs=[
        EffectSpec(id=5, owner_kind="ability", owner_id=903, atom_type="rule-modifier",
                     params={"scope": "self", "associations_allowed": False}),
    ])
    plain = _place(state, "p1", Zone.ATTACKING, name="plain")

    assert effects.get_association_limit(state, teamwork) == 2
    assert effects.get_association_limit(state, plain) == 1  # default
    assert effects.associations_allowed(state, loner) is False
    assert effects.associations_allowed(state, plain) is True


def test_incoming_damage_modifier_filters_by_element() -> None:
    state = _empty_state()
    card = _place(state, "p1", Zone.ATTACKING, name="dry", ability_ids=[904], specs=[
        EffectSpec(id=6, owner_kind="ability", owner_id=904, atom_type="incoming-damage-modifier",
                     params={"scope": "self", "attack_element_id": 3, "delta": 10}),
    ])
    attacker = _place(state, "p2", Zone.ATTACKING, name="atk")

    water = effects.get_incoming_damage_modifier(state, card, _attack(element_id=3), attacker)
    fire = effects.get_incoming_damage_modifier(state, card, _attack(element_id=5), attacker)
    assert water == 10
    assert fire == 0


def test_stat_modifier_per_named_card_scales_and_does_not_drift() -> None:
    state = _empty_state()
    _place(state, "p1", Zone.ATTACKING, name="Nyx", character_name="Nyx", ability_ids=[905], specs=[
        EffectSpec(id=10, owner_kind="ability", owner_id=905, atom_type="stat-modifier-per-named-card",
                     params={"scope": "allies_active", "damage_type": "magical", "defense_per": 20, "character_name": "Moira"}),
    ])
    moira = _place(state, "p1", Zone.ATTACKING, name="Moira", character_name="Moira")
    _place(state, "p1", Zone.SUPPORTING, name="Moira2", character_name="Moira")

    magical = _attack(type_=DamageType.MAGICAL)
    # +20 magical defense per Moira on the field (two), applied only to Moira targets.
    assert effects.get_passive_stat_modifiers(state, moira, attack=magical)["defense_bonus"] == 40
    # Querying again must yield the same result: the atom must not mutate its own params.
    assert effects.get_passive_stat_modifiers(state, moira, attack=magical)["defense_bonus"] == 40


def test_registry_covers_every_atom_type() -> None:
    # Every registered class is keyed by its own atom_type.
    for atom_type, cls in effects.EFFECT_REGISTRY.items():
        assert cls.atom_type == atom_type


def _run_all() -> None:
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  ok: {name}")


if __name__ == "__main__":
    _run_all()
    print("OK: effect unit tests passed")
