"""
Data-driven effect atom runtime.

Catalog rows in the `effects` table are copied into GameCardInput during deck
enrichment, then instantiated into EffectAtom objects when GameCard instances
are created. Triggered atoms emit events on game triggers; passive atoms
contribute to a PassiveQueryResult at validation/damage-calculation time.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, Any, Optional

from app.models.game.enums import Zone, DamageType, StatusType
from app.models.game.events import (
    GameEvent,
    CardAssociatedEvent,
    CardDestroyedEvent,
    CardExiledEvent,
    CardHealthChangedEvent,
    CardSwappedEvent,
    DamageDealtEvent,
    DiceRolledEvent,
    ForcedSwapRequestedEvent,
    HealingAppliedEvent,
    StatusAppliedEvent,
    AttackDeclaredEvent,
    AttackResolvedEvent,
)

if TYPE_CHECKING:
    from app.models.game.attack import AttackDefinition
    from app.models.game.card import EffectSpec, GameCard
    from app.models.game.state import GameState


class EffectTrigger(Enum):
    ON_PLAY = auto()
    ON_PROMOTE = auto()
    ON_DESTROY = auto()
    ON_ATTACK = auto()
    ON_DEFEND = auto()
    ON_DEAL_DAMAGE = auto()
    ON_TAKE_DAMAGE = auto()
    ON_TURN_START = auto()
    ON_TURN_END = auto()
    ON_DRAW = auto()
    ON_ANY_PLAY = auto()
    ON_ANY_DESTROY = auto()
    ON_ASSOCIATE = auto()
    ON_ASSOCIATE_TARGET = auto()
    ON_ALLY_ATTACK = auto()
    ON_ATTACK_RESOLVE = auto()
    PASSIVE = auto()


class PassiveCategory(str, Enum):
    STAT_MODIFIER = "STAT_MODIFIER"
    INCOMING_DAMAGE_MODIFIER = "INCOMING_DAMAGE_MODIFIER"
    IMMUNITY = "IMMUNITY"
    ASSOCIATION_RULES = "ASSOCIATION_RULES"
    ATTACK_COOLDOWN = "ATTACK_COOLDOWN"
    ATTACK_SHAPE = "ATTACK_SHAPE"
    ATTACK_COST = "ATTACK_COST"
    ASSOCIATION_TARGET_FILTER = "ASSOCIATION_TARGET_FILTER"
    REVIVE_RULE = "REVIVE_RULE"


@dataclass
class EffectContext:
    """Context for a triggered atom reacting to a single event."""
    state: "GameState"
    source_card: "GameCard"
    trigger_event: Optional[GameEvent] = None
    trigger: Optional[EffectTrigger] = None


@dataclass
class EffectResult:
    """Events produced by a triggered atom."""
    events: list[GameEvent] = field(default_factory=list)


@dataclass(frozen=True)
class PassiveContext:
    """Inputs a passive atom inspects while contributing to a query."""
    state: "GameState"
    source_card: "GameCard"
    host_card: Optional["GameCard"] = None
    target_card: Optional["GameCard"] = None
    attack: Optional["AttackDefinition"] = None
    attacker: Optional["GameCard"] = None
    effect_kind: Optional[str] = None


@dataclass
class PassiveSource:
    source_card: "GameCard"
    atom: "EffectAtom"
    host_card: Optional["GameCard"] = None


@dataclass
class PassiveQueryResult:
    attack_bonus: int = 0
    defense_bonus: int = 0
    health_bonus: int = 0
    attack_multiplier: float = 1.0
    defense_override: Optional[int] = None
    incoming_damage_modifier: int = 0
    immune: bool = False
    association_forbidden: bool = False
    association_limit: Optional[int] = None
    attack_cooldown: int = 0
    revive_from_graveyard: bool = False
    errors: list[str] = field(default_factory=list)

    @property
    def final_defense_bonus(self) -> int:
        return self.defense_override if self.defense_override is not None else self.defense_bonus


class EffectAtom:
    """Base class for a single configured effect atom.

    Subclasses set ``atom_type`` (matching a row's ``atom_type``) and either
    override ``execute`` (triggered atoms) or ``contribute_passive`` (passive
    atoms) plus the relevant ``passive_categories``/``default_triggers``.
    """

    atom_type: str = "base"
    default_triggers: tuple[EffectTrigger, ...] = ()
    passive_categories: tuple[PassiveCategory, ...] = ()

    def __init__(self, spec: "EffectSpec"):
        self.id = spec.id
        self.owner_kind = spec.owner_kind
        self.owner_id = spec.owner_id
        self.trigger_name = spec.trigger
        self.sort_order = spec.sort_order
        self.script_id = spec.script_id
        self.params: dict[str, Any] = dict(spec.params or {})

    @property
    def triggers(self) -> list[EffectTrigger]:
        triggers = list(self.default_triggers)
        if self.trigger_name:
            trigger = EffectTrigger[self.trigger_name]
            if trigger not in triggers:
                triggers.append(trigger)
        return triggers

    def should_trigger(self, context: EffectContext) -> bool:
        event = context.trigger_event
        if self.owner_kind == "attack" and hasattr(event, "attack_id"):
            return getattr(event, "attack_id") == self.owner_id
        if self.owner_kind == "association":
            if isinstance(event, CardAssociatedEvent):
                return context.source_card.instance_id == event.association_card_id and self.owner_id in context.source_card.association_ids
            return self.owner_id in context.source_card.association_ids
        if self.owner_kind == "ability":
            return self.owner_id in context.source_card.ability_ids
        return True

    def execute(self, context: EffectContext) -> EffectResult:
        return EffectResult()

    def contribute_passive(self, result: PassiveQueryResult, ctx: PassiveContext) -> None:
        return None


# ── Shared helpers ───────────────────────────────────────────────────────

def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _has_any_element(card: Optional["GameCard"], values: Any) -> bool:
    if not card:
        return False
    ids = {int(v) for v in _as_list(values)}
    return bool(ids.intersection(card.element_ids))


def _damage_type_matches(params: dict[str, Any], attack: Optional["AttackDefinition"]) -> bool:
    values = _as_list(params.get("damage_type")) + _as_list(params.get("damage_types"))
    if not values:
        return True
    if not attack:
        return False
    return attack.type.value.lower() in {str(v).lower() for v in values}


def _matches_card_filter(params: dict[str, Any], card: Optional["GameCard"]) -> bool:
    if not card:
        return False
    if params.get("filter_element_id") and not _has_any_element(card, params["filter_element_id"]):
        return False
    if params.get("filter_element_ids") and not _has_any_element(card, params["filter_element_ids"]):
        return False
    if params.get("target_filter_element_id") and not _has_any_element(card, params["target_filter_element_id"]):
        return False
    if params.get("target_filter_type_id") and card.type_id != int(params["target_filter_type_id"]):
        return False
    if params.get("filter_type_id") and card.type_id != int(params["filter_type_id"]):
        return False
    name = params.get("character_name") or params.get("card_name")
    if name and name.lower() not in {card.name.lower(), (card.character_name or "").lower()}:
        return False
    if params.get("zone") and card.zone.value.lower() != str(params["zone"]).lower():
        return False
    return True


def _scope_affects(ctx: PassiveContext, params: dict[str, Any]) -> bool:
    """Whether ``ctx.target_card`` is in this atom's configured scope."""
    target, source = ctx.target_card, ctx.source_card
    if not target:
        return False
    scope = params.get("scope", "self")
    if scope in ("self", "source"):
        return target.instance_id == source.instance_id
    if scope in ("host", "associated_host", "associated_target"):
        return ctx.host_card is not None and target.instance_id == ctx.host_card.instance_id
    if scope in ("allies_active", "allies"):
        return target.owner_id == source.owner_id and target.zone in (Zone.SUPPORTING, Zone.ATTACKING)
    if scope == "all_active":
        return target.zone in (Zone.SUPPORTING, Zone.ATTACKING)
    if scope == "enemies_active":
        return target.owner_id != source.owner_id and target.zone in (Zone.SUPPORTING, Zone.ATTACKING)
    return False


def _active_cards(state: "GameState") -> list["GameCard"]:
    cards: list["GameCard"] = []
    for player in state.room.players.values():
        for card_id in player.get_active_cards():
            if card := state.cards.get(card_id):
                cards.append(card)
    return cards


def _named_card_count(state: "GameState", name: str) -> int:
    needle = name.lower()
    return sum(
        1 for card in _active_cards(state)
        if needle in {card.name.lower(), (card.character_name or "").lower()}
    )


def _status_payload(required_face: int | None = None, **extra: Any) -> dict[str, Any]:
    payload = dict(extra)
    if required_face is not None:
        payload["required_face"] = required_face
    return payload


def _health_delta_events(state: "GameState", target: "GameCard", source: "GameCard", delta: int, reason: str) -> list[GameEvent]:
    """A health change plus a destruction event when it drops the card to 0."""
    new_health = target.current_health + delta
    events: list[GameEvent] = [
        CardHealthChangedEvent(
            game_id=state.game_id,
            target_id=target.instance_id,
            source_id=source.instance_id,
            delta=delta,
            new_health=new_health,
            reason=reason,
        )
    ]
    if new_health <= 0:
        events.append(CardDestroyedEvent(
            game_id=state.game_id,
            instance_id=target.instance_id,
            owner_id=target.owner_id,
            card_name=target.name,
            destroyed_by=source.instance_id,
        ))
    return events


# ── Passive atoms ──────────────────────────────────────────────────────────

class StatModifierAtom(EffectAtom):
    atom_type = "stat-modifier"
    passive_categories = (PassiveCategory.STAT_MODIFIER,)

    def contribute_passive(self, result: PassiveQueryResult, ctx: PassiveContext) -> None:
        self._apply(result, ctx, self.params)

    def _apply(self, result: PassiveQueryResult, ctx: PassiveContext, params: dict[str, Any]) -> None:
        if params.get("every_n_turns") and ctx.state.turn_number % int(params["every_n_turns"]) != 0:
            return
        if not _scope_affects(ctx, params):
            return
        if not _matches_card_filter(params, ctx.target_card):
            return
        if not _damage_type_matches(params, ctx.attack):
            return

        attack = ctx.attack
        result.attack_bonus += int(params.get("attack") or 0)
        result.health_bonus += int(params.get("health") or 0)
        defense = int(params.get("defense") or 0)
        if attack and attack.type == DamageType.PHYSICAL:
            defense += int(params.get("physical_defense") or 0)
        elif attack and attack.type == DamageType.MAGICAL:
            defense += int(params.get("magical_defense") or 0)
        result.defense_bonus += defense
        if params.get("multiplier"):
            result.attack_multiplier *= float(params["multiplier"])
        if params.get("defense_override") is not None:
            result.defense_override = int(params["defense_override"])


class StatModifierPerNamedCardAtom(StatModifierAtom):
    """Stat modifier whose attack/defense scale with the count of a named card on the field."""
    atom_type = "stat-modifier-per-named-card"

    def contribute_passive(self, result: PassiveQueryResult, ctx: PassiveContext) -> None:
        name = self.params.get("character_name") or self.params.get("card_name")
        if not name:
            return
        count = _named_card_count(ctx.state, name)
        if count == 0:
            return
        params = dict(self.params)
        if params.get("defense_per"):
            params["defense"] = int(params.get("defense", 0)) + int(params["defense_per"]) * count
        if params.get("attack_per"):
            params["attack"] = int(params.get("attack", 0)) + int(params["attack_per"]) * count
        self._apply(result, ctx, params)


class IncomingDamageModifierAtom(EffectAtom):
    atom_type = "incoming-damage-modifier"
    passive_categories = (PassiveCategory.INCOMING_DAMAGE_MODIFIER,)

    def contribute_passive(self, result: PassiveQueryResult, ctx: PassiveContext) -> None:
        if not ctx.attack or not _scope_affects(ctx, self.params):
            return
        if self.params.get("attack_element_id") and ctx.attack.element_id != int(self.params["attack_element_id"]):
            return
        result.incoming_damage_modifier += int(self.params.get("delta") or 0)


class ImmunityAtom(EffectAtom):
    atom_type = "immunity"
    passive_categories = (PassiveCategory.IMMUNITY,)

    def contribute_passive(self, result: PassiveQueryResult, ctx: PassiveContext) -> None:
        params = self.params
        if not _scope_affects(ctx, params) or not _matches_card_filter(params, ctx.target_card):
            return
        if params.get("enemy_damage_type"):
            if not ctx.attack or ctx.attack.type.value.lower() != str(params["enemy_damage_type"]).lower():
                return
        if params.get("immune_element_id") and ctx.attack and ctx.attack.element_id != int(params["immune_element_id"]):
            return
        if params.get("immune_kind") and ctx.effect_kind and str(params["immune_kind"]).lower() != ctx.effect_kind.lower():
            return
        result.immune = True


class RuleModifierAtom(EffectAtom):
    atom_type = "rule-modifier"
    passive_categories = (
        PassiveCategory.ASSOCIATION_RULES,
        PassiveCategory.ATTACK_COOLDOWN,
        PassiveCategory.REVIVE_RULE,
    )

    def contribute_passive(self, result: PassiveQueryResult, ctx: PassiveContext) -> None:
        params = self.params
        if not _scope_affects(ctx, params):
            return
        if params.get("associations_allowed") is False:
            result.association_forbidden = True
        if params.get("max_associations") is not None:
            result.association_limit = max(result.association_limit or 1, int(params["max_associations"]))
        if params.get("attack_cooldown_turns") is not None:
            result.attack_cooldown = max(result.attack_cooldown, int(params["attack_cooldown_turns"]))
        if params.get("can_revive_from_graveyard"):
            result.revive_from_graveyard = True


class AttackCooldownAtom(RuleModifierAtom):
    atom_type = "attack-cooldown"


class AssociationTargetFilterAtom(EffectAtom):
    atom_type = "association-target-filter"
    passive_categories = (PassiveCategory.ASSOCIATION_TARGET_FILTER,)

    def contribute_passive(self, result: PassiveQueryResult, ctx: PassiveContext) -> None:
        if ctx.target_card and not _matches_card_filter(self.params, ctx.target_card):
            result.errors.append("Association target does not match effect requirements")


class AttackShapeAtom(EffectAtom):
    """Marker atom: the attack hits every enemy in the attacking zone."""
    atom_type = "multi-target-zone"
    passive_categories = (PassiveCategory.ATTACK_SHAPE,)


class AttackCostAtom(EffectAtom):
    """Marker atom: the attack costs exiling a graveyard ally (paid in AttackAction)."""
    atom_type = "exile-graveyard-ally-cost"
    passive_categories = (PassiveCategory.ATTACK_COST,)


# ── Triggered atoms ──────────────────────────────────────────────────────

class SplashAdjacentAtom(EffectAtom):
    atom_type = "splash-adjacent"
    default_triggers = (EffectTrigger.ON_ATTACK_RESOLVE,)

    def execute(self, context: EffectContext) -> EffectResult:
        event = context.trigger_event
        if not isinstance(event, AttackResolvedEvent) or event.final_damage <= 0:
            return EffectResult()
        params = self.params
        target = context.state.get_card(event.target_id)
        secondary = context.state.get_card(event.secondary_target_id)
        if not target or not secondary:
            return EffectResult()
        if params.get("exclude_target_element_id") and _has_any_element(target, params["exclude_target_element_id"]):
            return EffectResult()
        amount = math.floor(event.final_damage * float(params.get("fraction", 0.5)))
        return EffectResult(events=_health_delta_events(context.state, secondary, context.source_card, -amount, "splash"))


class ApplyStatusAtom(EffectAtom):
    atom_type = "apply-status"
    default_triggers = (EffectTrigger.ON_ATTACK_RESOLVE,)

    def execute(self, context: EffectContext) -> EffectResult:
        return self._apply(context, self.params)

    def _apply(self, context: EffectContext, params: dict[str, Any]) -> EffectResult:
        event = context.trigger_event
        if not isinstance(event, (AttackResolvedEvent, DamageDealtEvent, CardAssociatedEvent)):
            return EffectResult()
        target_id = getattr(event, "target_id", None) or getattr(event, "target_card_id", "")
        target = context.state.get_card(target_id)
        if not target:
            return EffectResult()
        if params.get("immune_element_id") and _has_any_element(target, params["immune_element_id"]):
            return EffectResult()

        events: list[GameEvent] = []
        if params.get("dice_face") is not None:
            faces = int(params.get("faces", 6))
            roll = random.randint(1, faces)
            events.append(DiceRolledEvent(
                game_id=context.state.game_id,
                roller_id=context.source_card.owner_id,
                faces=faces,
                result=roll,
                purpose=str(params.get("purpose", "apply_status")),
            ))
            if roll != int(params["dice_face"]):
                return EffectResult(events=events)

        status_type = StatusType(str(params.get("status_type", StatusType.BLOCK_ATTACK.value)))
        events.append(StatusAppliedEvent(
            game_id=context.state.game_id,
            target_id=target.instance_id,
            source_card_id=context.source_card.instance_id,
            source_atom_id=self.id,
            status_type=status_type,
            duration_turns=int(params.get("duration_turns", 1)),
            tick_on=str(params.get("tick_on", "none")),
            expires_on=str(params.get("expires_on", "own_turn_end")),
            payload=_status_payload(params.get("required_face"), **dict(params.get("payload", {}))),
        ))
        return EffectResult(events=events)


class DamageOverTimeAtom(ApplyStatusAtom):
    atom_type = "damage-over-time"

    def execute(self, context: EffectContext) -> EffectResult:
        params = dict(self.params)
        params["status_type"] = StatusType.DAMAGE_OVER_TIME.value
        params.setdefault("tick_on", "own_turn_start")
        params.setdefault("expires_on", "none")
        params["payload"] = {
            **dict(params.get("payload", {})),
            "amount": int(params.get("amount", 10)),
            "delay_turns": int(params.get("delay_turns", 0)),
        }
        return self._apply(context, params)


class OnTakeDamagePunishAtom(EffectAtom):
    atom_type = "on-take-damage-punish"
    default_triggers = (EffectTrigger.ON_TAKE_DAMAGE,)

    def execute(self, context: EffectContext) -> EffectResult:
        event = context.trigger_event
        if not isinstance(event, DamageDealtEvent) or event.final_damage <= 0:
            return EffectResult()
        attacker = context.state.get_card(event.source_id)
        if not attacker:
            return EffectResult()
        excluded = self.params.get("exclude_attacker_element_id") or self.params.get("exclude_attacker_element_ids")
        if excluded and _has_any_element(attacker, excluded):
            return EffectResult()
        delta = int(self.params.get("attacker_health_delta", -10))
        return EffectResult(events=_health_delta_events(context.state, attacker, context.source_card, delta, "counter_effect"))


class OnTakeDamageStatusAtom(EffectAtom):
    atom_type = "on-take-damage-status"
    default_triggers = (EffectTrigger.ON_TAKE_DAMAGE,)

    def execute(self, context: EffectContext) -> EffectResult:
        event = context.trigger_event
        if not isinstance(event, DamageDealtEvent) or event.final_damage <= 0:
            return EffectResult()
        attacker = context.state.get_card(event.source_id)
        if not attacker:
            return EffectResult()
        excluded = self.params.get("exclude_attacker_element_id") or self.params.get("exclude_attacker_element_ids")
        if excluded and _has_any_element(attacker, excluded):
            return EffectResult()
        status_type = StatusType(str(self.params.get("status_type", StatusType.BLOCK_ATTACK.value)))
        return EffectResult(events=[StatusAppliedEvent(
            game_id=context.state.game_id,
            target_id=attacker.instance_id,
            source_card_id=context.source_card.instance_id,
            source_atom_id=self.id,
            status_type=status_type,
            duration_turns=int(self.params.get("duration_turns", 1)),
            expires_on=str(self.params.get("expires_on", "own_turn_end")),
            payload=_status_payload(self.params.get("required_face")),
        )])


class HealAtom(EffectAtom):
    atom_type = "self-heal-scaled"
    default_triggers = (EffectTrigger.ON_ATTACK_RESOLVE,)

    def execute(self, context: EffectContext) -> EffectResult:
        event = context.trigger_event
        if not isinstance(event, AttackResolvedEvent) or event.final_damage <= 0:
            return EffectResult()
        source = context.source_card
        target = context.state.get_card(event.target_id)
        amount = int(self.params.get("base_heal", 0))
        if target and _has_any_element(target, self.params.get("bonus_target_element_ids")):
            amount += int(self.params.get("bonus_heal", 0))
        if amount <= 0:
            return EffectResult()
        new_health = min(source.health, source.current_health + amount)
        return EffectResult(events=[HealingAppliedEvent(
            game_id=context.state.game_id,
            target_id=source.instance_id,
            source_id=source.instance_id,
            amount=new_health - source.current_health,
            new_health=new_health,
        )])


class SelfDamageAtom(EffectAtom):
    atom_type = "self-damage"
    default_triggers = (EffectTrigger.ON_ATTACK_RESOLVE,)

    def execute(self, context: EffectContext) -> EffectResult:
        if not isinstance(context.trigger_event, AttackResolvedEvent):
            return EffectResult()
        amount = int(self.params.get("amount", 0))
        if amount <= 0:
            return EffectResult()
        return EffectResult(events=_health_delta_events(context.state, context.source_card, context.source_card, -amount, "self_damage"))


class ForcedSwapAtom(EffectAtom):
    atom_type = "force-swap-on-high-damage"
    default_triggers = (EffectTrigger.ON_ATTACK_RESOLVE,)

    def execute(self, context: EffectContext) -> EffectResult:
        event = context.trigger_event
        if not isinstance(event, AttackResolvedEvent):
            return EffectResult()
        threshold = int(self.params.get("threshold", 100))
        target = context.state.get_card(event.target_id)
        if not target or event.final_damage <= threshold or event.target_destroyed:
            return EffectResult()
        defender = context.state.room.players[target.owner_id]
        if not defender.zones[Zone.SUPPORTING.name].card_ids:
            return EffectResult()
        return EffectResult(events=[ForcedSwapRequestedEvent(
            game_id=context.state.game_id,
            owner_id=target.owner_id,
            target_card_id=target.instance_id,
            source_card_id=context.source_card.instance_id,
        )])


class AllyFollowupAttackAtom(EffectAtom):
    atom_type = "ally-attack-rider"
    default_triggers = (EffectTrigger.ON_ALLY_ATTACK,)

    def execute(self, context: EffectContext) -> EffectResult:
        event = context.trigger_event
        source = context.source_card
        if not isinstance(event, AttackDeclaredEvent):
            return EffectResult()
        if source.zone != Zone.SUPPORTING or event.attacker_id == source.instance_id:
            return EffectResult()
        target = context.state.get_card(event.target_id)
        if not target or target.owner_id == source.owner_id or not source.attacks:
            return EffectResult()
        fraction = float(self.params.get("fraction", 1 / 3))
        amount = max(0, math.floor(source.attacks[0].damage * fraction))
        return EffectResult(events=_health_delta_events(context.state, target, source, -amount, "ally_followup"))


class OnAssociateGrantThenExileAtom(EffectAtom):
    atom_type = "on-associate-grant-then-exile"
    default_triggers = (EffectTrigger.ON_ASSOCIATE, EffectTrigger.ON_ATTACK)

    def execute(self, context: EffectContext) -> EffectResult:
        event = context.trigger_event
        source = context.source_card
        if isinstance(event, CardAssociatedEvent):
            host = context.state.get_card(event.target_card_id)
            amount = int(self.params.get("health", 0))
            if not host or amount <= 0:
                return EffectResult()
            return EffectResult(events=[CardHealthChangedEvent(
                game_id=context.state.game_id,
                target_id=host.instance_id,
                source_id=source.instance_id,
                delta=amount,
                new_health=host.current_health + amount,
                reason="association_health",
            )])
        if isinstance(event, AttackDeclaredEvent):
            if source.association_target_id != event.attacker_id:
                return EffectResult()
            return EffectResult(events=[CardDestroyedEvent(
                game_id=context.state.game_id,
                instance_id=source.instance_id,
                owner_id=source.owner_id,
                card_name=source.name,
                destroyed_by=event.attacker_id,
            )])
        return EffectResult()


class ScriptAtom(EffectAtom):
    atom_type = "script"
    default_triggers = (EffectTrigger.ON_ASSOCIATE,)

    def execute(self, context: EffectContext) -> EffectResult:
        script = SCRIPT_REGISTRY.get(self.script_id) if self.script_id else None
        if not script:
            return EffectResult()
        return EffectResult(events=script(context, self))


# ── Registered scripts ───────────────────────────────────────────────────

def _script_cambio_de_guardia(context: EffectContext, atom: EffectAtom) -> list[GameEvent]:
    event = context.trigger_event
    if not isinstance(event, CardAssociatedEvent):
        return []
    target = context.state.get_card(event.target_card_id)
    supporting = context.state.get_card(event.swap_with_supporting_card_id)
    if not target or target.zone != Zone.ATTACKING or not supporting or supporting.zone != Zone.SUPPORTING:
        return []
    return [
        CardSwappedEvent(
            game_id=context.state.game_id,
            player_id=context.source_card.owner_id,
            supporting_card_id=supporting.instance_id,
            attacking_card_id=target.instance_id,
        ),
        CardExiledEvent(
            game_id=context.state.game_id,
            instance_id=context.source_card.instance_id,
            owner_id=context.source_card.owner_id,
            reason="cambio_de_guardia",
        ),
    ]


SCRIPT_REGISTRY = {
    "cambio_de_guardia": _script_cambio_de_guardia,
}


EFFECT_REGISTRY: dict[str, type[EffectAtom]] = {
    cls.atom_type: cls
    for cls in (
        StatModifierAtom,
        StatModifierPerNamedCardAtom,
        IncomingDamageModifierAtom,
        ImmunityAtom,
        RuleModifierAtom,
        AttackCooldownAtom,
        AssociationTargetFilterAtom,
        AttackShapeAtom,
        SplashAdjacentAtom,
        AttackCostAtom,
        ApplyStatusAtom,
        DamageOverTimeAtom,
        OnTakeDamagePunishAtom,
        OnTakeDamageStatusAtom,
        HealAtom,
        SelfDamageAtom,
        ForcedSwapAtom,
        AllyFollowupAttackAtom,
        ScriptAtom,
        OnAssociateGrantThenExileAtom,
    )
}


def build_effect_atoms(specs: list["EffectSpec"]) -> list[EffectAtom]:
    atoms: list[EffectAtom] = []
    for spec in sorted(specs, key=lambda s: (s.sort_order, s.id)):
        cls = EFFECT_REGISTRY.get(spec.atom_type)
        if not cls:
            raise ValueError(f"Unknown effect atom_type={spec.atom_type!r} effect_id={spec.id}")
        atoms.append(cls(spec))
    return atoms


# ── Passive query engine ─────────────────────────────────────────────────

def _iter_passive_sources(state: "GameState") -> list[PassiveSource]:
    sources: list[PassiveSource] = []
    for card in _active_cards(state):
        for atom in card.effect_atoms:
            sources.append(PassiveSource(source_card=card, atom=atom))
        for assoc_id in card.associations:
            assoc_card = state.cards.get(assoc_id)
            if not assoc_card:
                continue
            for atom in assoc_card.effect_atoms:
                if atom.owner_kind == "association":
                    sources.append(PassiveSource(source_card=assoc_card, atom=atom, host_card=card))
    return sources


def query_passive(
    state: "GameState",
    category: PassiveCategory,
    *,
    target_card: Optional["GameCard"] = None,
    attack: Optional["AttackDefinition"] = None,
    attacker: Optional["GameCard"] = None,
    effect_kind: Optional[str] = None,
) -> PassiveQueryResult:
    result = PassiveQueryResult()
    for source in _iter_passive_sources(state):
        if category not in source.atom.passive_categories:
            continue
        ctx = PassiveContext(
            state=state,
            source_card=source.source_card,
            host_card=source.host_card,
            target_card=target_card,
            attack=attack,
            attacker=attacker,
            effect_kind=effect_kind,
        )
        source.atom.contribute_passive(result, ctx)
    return result


def get_passive_stat_modifiers(state: "GameState", target_card: "GameCard", attack: Optional["AttackDefinition"] = None, attacker: Optional["GameCard"] = None) -> dict[str, Any]:
    result = query_passive(state, PassiveCategory.STAT_MODIFIER, target_card=target_card, attack=attack, attacker=attacker)
    return {
        "attack_bonus": result.attack_bonus,
        "defense_bonus": result.final_defense_bonus,
        "health_bonus": result.health_bonus,
        "attack_multiplier": result.attack_multiplier,
    }


def get_incoming_damage_modifier(state: "GameState", target_card: "GameCard", attack: "AttackDefinition", attacker: "GameCard") -> int:
    return query_passive(state, PassiveCategory.INCOMING_DAMAGE_MODIFIER, target_card=target_card, attack=attack, attacker=attacker).incoming_damage_modifier


def is_immune_to_attack(state: "GameState", target_card: "GameCard", attack: "AttackDefinition", attacker: "GameCard") -> bool:
    return query_passive(state, PassiveCategory.IMMUNITY, target_card=target_card, attack=attack, attacker=attacker).immune


def is_immune_to_effect(state: "GameState", target_card: "GameCard", source_card: "GameCard", effect_kind: str) -> bool:
    return query_passive(state, PassiveCategory.IMMUNITY, target_card=target_card, attacker=source_card, effect_kind=effect_kind).immune


def get_association_limit(state: "GameState", target_card: "GameCard") -> int:
    return query_passive(state, PassiveCategory.ASSOCIATION_RULES, target_card=target_card).association_limit or 1


def associations_allowed(state: "GameState", target_card: "GameCard") -> bool:
    return not query_passive(state, PassiveCategory.ASSOCIATION_RULES, target_card=target_card).association_forbidden


def get_attack_cooldown(state: "GameState", attacker: "GameCard", attack: "AttackDefinition") -> int:
    result = query_passive(state, PassiveCategory.ATTACK_COOLDOWN, target_card=attacker, attack=attack, attacker=attacker)
    cooldown = result.attack_cooldown
    for atom in get_attack_atoms(attacker, attack.attack_id, "attack-cooldown"):
        cooldown = max(cooldown, int(atom.params.get("attack_cooldown_turns", 0)))
    return cooldown


def can_revive_from_graveyard(state: "GameState", card: "GameCard") -> bool:
    return query_passive(state, PassiveCategory.REVIVE_RULE, target_card=card).revive_from_graveyard


# ── Attack-owned atom lookups ────────────────────────────────────────────

def get_attack_atoms(card: "GameCard", attack_id: int, atom_type: Optional[str] = None) -> list[EffectAtom]:
    atoms = [
        atom for atom in card.effect_atoms
        if atom.owner_kind == "attack" and atom.owner_id == attack_id and (atom_type is None or atom.atom_type == atom_type)
    ]
    return sorted(atoms, key=lambda atom: (atom.sort_order, atom.id))


def _first_attack_atom(card: "GameCard", attack_id: int, atom_type: str) -> Optional[EffectAtom]:
    atoms = get_attack_atoms(card, attack_id, atom_type)
    return atoms[0] if atoms else None


def attack_has_multi_target(card: "GameCard", attack_id: int) -> bool:
    return bool(get_attack_atoms(card, attack_id, "multi-target-zone"))


def get_attack_cost_atom(card: "GameCard", attack_id: int) -> Optional[EffectAtom]:
    return _first_attack_atom(card, attack_id, "exile-graveyard-ally-cost")


def get_splash_atom(card: "GameCard", attack_id: int) -> Optional[EffectAtom]:
    return _first_attack_atom(card, attack_id, "splash-adjacent")


# ── Association-owned atom lookups ───────────────────────────────────────

def validate_association_target(state: "GameState", assoc_card: "GameCard", target_card: "GameCard") -> list[str]:
    result = PassiveQueryResult()
    ctx = PassiveContext(state=state, source_card=assoc_card, target_card=target_card)
    for atom in assoc_card.effect_atoms:
        if atom.owner_kind == "association" and PassiveCategory.ASSOCIATION_TARGET_FILTER in atom.passive_categories:
            atom.contribute_passive(result, ctx)
    return result.errors


def association_allows_direct_from_hand(assoc_card: "GameCard") -> bool:
    for atom in assoc_card.effect_atoms:
        if atom.owner_kind == "association" and atom.atom_type == "script":
            if atom.params.get("playable_directly_from_hand") or atom.script_id == "cambio_de_guardia":
                return True
    return False


def graveyard_cost_candidates(state: "GameState", player_id: str, atom: EffectAtom) -> list["GameCard"]:
    excluded = atom.params.get("exclude_element_id") or atom.params.get("exclude_element_ids")
    player = state.room.players[player_id]
    candidates: list["GameCard"] = []
    for card_id in player.zones[Zone.GRAVEYARD.name].card_ids:
        card = state.cards.get(card_id)
        if not card:
            continue
        if excluded and _has_any_element(card, excluded):
            continue
        candidates.append(card)
    return candidates
