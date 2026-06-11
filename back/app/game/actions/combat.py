"""
Combat actions (Attack, ForceDefend) and shared combat event generation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.game.actions.base import Action
from app.game.effects import (
    attack_has_multi_target,
    can_revive_from_graveyard,
    get_attack_cooldown,
    get_attack_cost_atom,
    get_incoming_damage_modifier,
    get_passive_stat_modifiers,
    get_splash_atom,
    graveyard_cost_candidates,
    is_immune_to_attack,
)
from app.game.elements import calculate_damage
from app.models.game.enums import StatusType, TurnPhase, Zone
from app.models.game.events import (
    AttackDeclaredEvent,
    AttackResolvedEvent,
    CardDestroyedEvent,
    CardExiledEvent,
    CardPromotedEvent,
    CardRevivedEvent,
    CardSwappedEvent,
    DamageDealtEvent,
    DiceRolledEvent,
    ElementsConsumedEvent,
    GameEndedEvent,
    GameEvent,
    NoDefenderEvent,
    StatusExpiredEvent,
)

if TYPE_CHECKING:
    from app.game.validators import ValidationResult
    from app.models.game.card import GameCard
    from app.models.game.state import GameState


# ── Shared combat helper ────────────────────────────────────────────────


def _damage_and_destruction(
    state: GameState,
    source: GameCard,
    target: GameCard,
    attack,
    amount: int,
    base_damage: int = 0,
    element_bonus: int = 0,
    defense_reduction: int = 0,
) -> list[GameEvent]:
    """A DamageDealtEvent plus a CardDestroyedEvent when it drops the target to 0."""
    events: list[GameEvent] = [
        DamageDealtEvent(
            game_id=state.game_id,
            source_id=source.instance_id,
            target_id=target.instance_id,
            damage_type=attack.type,
            base_damage=base_damage,
            element_bonus=element_bonus,
            defense_reduction=defense_reduction,
            final_damage=amount,
            remaining_health=target.current_health - amount,
        )
    ]
    if target.current_health - amount <= 0:
        events.append(
            CardDestroyedEvent(
                game_id=state.game_id,
                instance_id=target.instance_id,
                owner_id=target.owner_id,
                card_name=target.name,
                destroyed_by=source.instance_id,
            )
        )
    return events


def build_combat_events(
    state: GameState,
    attacker: GameCard,
    target: GameCard,
    attack,
    attacker_owner_id: str,
    consume_elements: bool = True,
    secondary_target_id: str = "",
) -> list[GameEvent]:
    """Build element-consumption + attack-declared + damage + destruction events."""
    events: list[GameEvent] = []

    if consume_elements:
        element_costs = {c.element_id: c.amount for c in attack.necessary_force}
        if element_costs:
            events.append(
                ElementsConsumedEvent(
                    game_id=state.game_id,
                    player_id=attacker_owner_id,
                    elements=element_costs,
                    for_attack_id=attack.attack_id,
                )
            )

    events.append(
        AttackDeclaredEvent(
            game_id=state.game_id,
            attacker_owner_id=attacker_owner_id,
            attacker_id=attacker.instance_id,
            target_id=target.instance_id,
            attack_id=attack.attack_id,
            attack_name=attack.name,
            secondary_target_id=secondary_target_id,
        )
    )

    attacker_mods = get_passive_stat_modifiers(state, attacker, attack=attack, attacker=attacker)
    target_mods = get_passive_stat_modifiers(state, target, attack=attack, attacker=attacker)
    incoming_mod = get_incoming_damage_modifier(state, target, attack, attacker)
    effect_mod = attacker_mods["attack_bonus"] + incoming_mod - target_mods["defense_bonus"]
    damage_calc = calculate_damage(attack, attacker, target, effect_modifier=effect_mod)
    if attacker_mods.get("attack_multiplier", 1.0) != 1.0:
        damage_calc.final_damage = max(0, int(damage_calc.final_damage * attacker_mods["attack_multiplier"]))
    if is_immune_to_attack(state, target, attack, attacker):
        damage_calc.final_damage = 0
        damage_calc.reflected_damage = 0

    target_destroyed = target.current_health - damage_calc.final_damage <= 0 if damage_calc.final_damage > 0 else False
    if damage_calc.final_damage > 0:
        events.extend(
            _damage_and_destruction(
                state,
                attacker,
                target,
                attack,
                damage_calc.final_damage,
                base_damage=damage_calc.base_damage,
                element_bonus=damage_calc.element_bonus,
                defense_reduction=damage_calc.defense_value,
            )
        )

    if damage_calc.reflected_damage > 0:
        events.extend(_damage_and_destruction(state, target, attacker, attack, damage_calc.reflected_damage))

    events.append(
        AttackResolvedEvent(
            game_id=state.game_id,
            attacker_owner_id=attacker_owner_id,
            attacker_id=attacker.instance_id,
            target_id=target.instance_id,
            attack_id=attack.attack_id,
            attack_name=attack.name,
            final_damage=damage_calc.final_damage,
            target_destroyed=target_destroyed,
            secondary_target_id=secondary_target_id,
        )
    )

    return events


# ── Attack ──────────────────────────────────────────────────────────────


class AttackAction(Action):
    action_type: str = "attack"
    valid_phases: list[TurnPhase] | None = [TurnPhase.ATTACK]
    attacker_id: str = ""
    attack_id: int = 0
    target_card_id: str = ""
    secondary_target_card_id: str = ""
    cost_card_id: str = ""

    def validate(self, state: GameState) -> ValidationResult:
        from app.game.elements import can_afford_attack
        from app.game.validators import ValidationResult

        player = state.room.get_player(self.player_id)
        opponent = state.room.get_opponent(self.player_id)
        if state.is_first_turn(self.player_id):
            return ValidationResult(
                valid=False, error="Cannot attack on first turn", error_code="FIRST_TURN_RESTRICTION"
            )
        if self.attacker_id not in player.zones[Zone.ATTACKING.name].card_ids:
            return ValidationResult(
                valid=False, error="Attacker must be in attacking zone", error_code="ATTACKER_NOT_IN_ATTACKING"
            )
        attacker = state.get_card(self.attacker_id)
        if not attacker or not attacker.can_attack:
            return ValidationResult(valid=False, error="Card cannot attack", error_code="CANNOT_ATTACK")
        attack = next((a for a in attacker.attacks if a.attack_id == self.attack_id), None)
        if not attack:
            return ValidationResult(valid=False, error="Card does not have this attack", error_code="INVALID_ATTACK")
        blocked = next((s for s in attacker.active_statuses if s.status_type == StatusType.BLOCK_ATTACK), None)
        if blocked:
            return ValidationResult(
                valid=False, error="Card cannot attack due to status", error_code="ATTACK_BLOCKED_BY_STATUS"
            )
        cooldown = get_attack_cooldown(state, attacker, attack)
        if cooldown and state.turn_number - attacker.attack_last_used.get(attack.attack_id, -9999) <= cooldown:
            return ValidationResult(valid=False, error="Attack is on cooldown", error_code="ATTACK_ON_COOLDOWN")
        cost_atom = get_attack_cost_atom(attacker, attack.attack_id)
        if cost_atom:
            candidates = {card.instance_id for card in graveyard_cost_candidates(state, self.player_id, cost_atom)}
            if self.cost_card_id not in candidates:
                return ValidationResult(
                    valid=False,
                    error="This attack requires a valid graveyard card cost",
                    error_code="MISSING_ATTACK_COST",
                )
        if not can_afford_attack(
            {e: player.element_pool.get_available(e) for e in player.element_pool.elements}, attack
        ):
            return ValidationResult(valid=False, error="Not enough elements", error_code="INSUFFICIENT_ELEMENTS")
        opponent_attacking = opponent.zones[Zone.ATTACKING.name]
        if self.target_card_id not in opponent_attacking.card_ids:
            if len(opponent_attacking.card_ids) == 0:
                return ValidationResult(valid=True)
            return ValidationResult(
                valid=False, error="Target must be in opponent's attacking zone", error_code="INVALID_TARGET"
            )
        if not state.get_card(self.target_card_id):
            return ValidationResult(valid=False, error="Target card not found", error_code="TARGET_NOT_FOUND")
        splash_atom = get_splash_atom(attacker, attack.attack_id)
        if splash_atom:
            secondary_options = {
                card.instance_id for card in _get_adjacent_targets(state, opponent, self.target_card_id)
            }
            if len(secondary_options) > 1 and self.secondary_target_card_id not in secondary_options:
                return ValidationResult(
                    valid=False, error="Secondary splash target required", error_code="MISSING_SECONDARY_TARGET"
                )
            if self.secondary_target_card_id and self.secondary_target_card_id not in secondary_options:
                return ValidationResult(
                    valid=False, error="Invalid secondary target", error_code="INVALID_SECONDARY_TARGET"
                )
        return ValidationResult(valid=True)

    def to_events(self, state: GameState) -> list[GameEvent]:
        opponent = state.room.get_opponent(self.player_id)
        attacker = state.cards[self.attacker_id]
        attack = next(a for a in attacker.attacks if a.attack_id == self.attack_id)

        dice_events, dice_can_continue = self._dice_lock_events(attacker, state)
        if not dice_can_continue:
            return dice_events

        prefix_events: list[GameEvent] = list(dice_events)
        cost_atom = get_attack_cost_atom(attacker, attack.attack_id)
        if cost_atom and self.cost_card_id:
            cost_card = state.get_card(self.cost_card_id)
            if cost_card:
                prefix_events.append(
                    CardExiledEvent(
                        game_id=state.game_id,
                        instance_id=cost_card.instance_id,
                        owner_id=cost_card.owner_id,
                        reason="attack_cost",
                    )
                )

        if len(opponent.zones[Zone.ATTACKING.name].card_ids) == 0:
            if len(opponent.zones[Zone.SUPPORTING.name].card_ids) > 0:
                return [
                    *prefix_events,
                    NoDefenderEvent(
                        game_id=state.game_id,
                        defender_id=opponent.player_id,
                        attacker_id=self.player_id,
                        must_defend=True,
                        game_lost=False,
                        pending_attacker_card_id=self.attacker_id,
                        pending_attack_id=self.attack_id,
                        pending_attacker_owner_id=self.player_id,
                    ),
                ]
            else:
                return [
                    *prefix_events,
                    NoDefenderEvent(
                        game_id=state.game_id,
                        defender_id=opponent.player_id,
                        attacker_id=self.player_id,
                        must_defend=False,
                        game_lost=True,
                    ),
                    GameEndedEvent(
                        game_id=state.game_id,
                        winner_id=self.player_id,
                        loser_id=opponent.player_id,
                        reason="No defenders available",
                    ),
                ]

        target = state.cards[self.target_card_id]
        targets = [target]
        consume_first_only = True
        if attack_has_multi_target(attacker, attack.attack_id):
            targets = [
                card
                for cid in opponent.zones[Zone.ATTACKING.name].card_ids
                if (card := state.get_card(cid)) is not None
            ]
        secondary_target_id = self.secondary_target_card_id
        if not secondary_target_id:
            adjacent = _get_adjacent_targets(state, opponent, target.instance_id)
            if len(adjacent) == 1:
                secondary_target_id = adjacent[0].instance_id

        events = list(prefix_events)
        for idx, tgt in enumerate(targets):
            events.extend(
                build_combat_events(
                    state,
                    attacker,
                    tgt,
                    attack,
                    self.player_id,
                    consume_elements=consume_first_only and idx == 0,
                    secondary_target_id=secondary_target_id if tgt.instance_id == target.instance_id else "",
                )
            )
        return events

    def _dice_lock_events(self, attacker: GameCard, state: GameState) -> tuple[list[GameEvent], bool]:
        status = next((s for s in attacker.active_statuses if s.status_type == StatusType.DICE_LOCKED_ATTACK), None)
        if not status:
            return [], True
        required = int(status.payload.get("required_face", 3))
        result = state.rng.randint(1, int(status.payload.get("faces", 6)))
        events: list[GameEvent] = [
            DiceRolledEvent(
                game_id=state.game_id, roller_id=attacker.owner_id, faces=6, result=result, purpose="dice_locked_attack"
            )
        ]
        if result == required:
            events.append(
                StatusExpiredEvent(game_id=state.game_id, target_id=attacker.instance_id, status_id=status.status_id)
            )
            return events, True
        return events, False

    @classmethod
    def get_valid(cls, state: GameState, player_id: str) -> list[Action]:
        if state.is_first_turn(player_id):
            return []
        player = state.room.players[player_id]
        opponent = next((p for pid, p in state.room.players.items() if pid != player_id), None)
        if not opponent:
            return []
        actions: list[Action] = []
        for attacker_id in player.zones[Zone.ATTACKING.name].card_ids:
            attacker = state.get_card(attacker_id)
            if not attacker or not attacker.can_attack:
                continue
            for attack in attacker.attacks:
                if not all(player.element_pool.get_available(c.element_id) >= c.amount for c in attack.necessary_force):
                    continue
                cost_atom = get_attack_cost_atom(attacker, attack.attack_id)
                cost_ids = [""]
                if cost_atom:
                    cost_ids = [card.instance_id for card in graveyard_cost_candidates(state, player_id, cost_atom)]
                    if not cost_ids:
                        continue
                for target_id in opponent.zones[Zone.ATTACKING.name].card_ids:
                    secondary_options = (
                        _get_adjacent_targets(state, opponent, target_id)
                        if get_splash_atom(attacker, attack.attack_id)
                        else []
                    )
                    secondary_ids = [card.instance_id for card in secondary_options] or [""]
                    for cost_id in cost_ids:
                        for secondary_id in secondary_ids:
                            actions.append(
                                cls(
                                    player_id=player_id,
                                    attacker_id=attacker_id,
                                    attack_id=attack.attack_id,
                                    target_card_id=target_id,
                                    secondary_target_card_id=secondary_id,
                                    cost_card_id=cost_id,
                                )
                            )
                if len(opponent.zones[Zone.ATTACKING.name].card_ids) == 0:
                    for cost_id in cost_ids:
                        actions.append(
                            cls(
                                player_id=player_id,
                                attacker_id=attacker_id,
                                attack_id=attack.attack_id,
                                target_card_id="",
                                cost_card_id=cost_id,
                            )
                        )
        return actions


def _get_adjacent_targets(state: GameState, opponent, target_id: str) -> list[GameCard]:
    ids = opponent.zones[Zone.ATTACKING.name].card_ids
    if target_id not in ids:
        return []
    idx = ids.index(target_id)
    candidates = []
    for n in (idx - 1, idx + 1):
        if 0 <= n < len(ids):
            card = state.get_card(ids[n])
            if card:
                candidates.append(card)
    return candidates


# ── Force Defend ────────────────────────────────────────────────────────


class ForceDefendAction(Action):
    action_type: str = "force_defend"
    valid_phases: list[TurnPhase] | None = [TurnPhase.ATTACK]
    instance_id: str = ""

    def validate(self, state: GameState) -> ValidationResult:
        from app.game.validators import ValidationResult

        if state.pending_action != "force_defend":
            return ValidationResult(valid=False, error="No force defend pending", error_code="NO_FORCE_DEFEND")
        player = state.room.get_player(self.player_id)
        if self.instance_id not in player.zones[Zone.SUPPORTING.name].card_ids:
            return ValidationResult(
                valid=False, error="Card must be in supporting zone", error_code="CARD_NOT_IN_SUPPORTING"
            )
        if player.zones[Zone.ATTACKING.name].is_full:
            return ValidationResult(valid=False, error="Attacking zone is full", error_code="ATTACKING_ZONE_FULL")
        return ValidationResult(valid=True)

    def to_events(self, state: GameState) -> list[GameEvent]:
        events: list[GameEvent] = []
        card = state.get_card(self.instance_id)
        if card:
            events.append(
                CardPromotedEvent(
                    game_id=state.game_id,
                    player_id=self.player_id,
                    instance_id=self.instance_id,
                    card_id=card.card_id,
                    card_name=card.name,
                )
            )
        if state.pending_attack and card:
            pending = state.pending_attack
            attacker = state.get_card(pending.attacker_id)
            attack = next((a for a in attacker.attacks if a.attack_id == pending.attack_id), None) if attacker else None
            if attacker and attack:
                events.extend(build_combat_events(state, attacker, card, attack, pending.attacker_owner_id))
        return events

    @classmethod
    def get_valid(cls, state: GameState, player_id: str) -> list[Action]:
        if state.pending_action != "force_defend":
            return []
        if state.pending_defender_id and state.pending_defender_id != player_id:
            return []
        player = state.room.players.get(player_id)
        if not player:
            return []
        if player.zones[Zone.ATTACKING.name].is_full:
            return []
        return [
            cls(player_id=player_id, instance_id=cid)
            for cid in player.zones[Zone.SUPPORTING.name].card_ids
            if state.get_card(cid)
        ]


class ResolveForcedSwapAction(Action):
    action_type: str = "resolve_forced_swap"
    valid_phases: list[TurnPhase] | None = None
    supporting_card_id: str = ""

    def validate(self, state: GameState) -> ValidationResult:
        from app.game.validators import ValidationResult

        if state.pending_action != "forced_swap" or state.pending_defender_id != self.player_id:
            return ValidationResult(valid=False, error="No forced swap pending", error_code="NO_FORCED_SWAP")
        player = state.room.get_player(self.player_id)
        if self.supporting_card_id not in player.zones[Zone.SUPPORTING.name].card_ids:
            return ValidationResult(
                valid=False, error="Card must be in supporting zone", error_code="CARD_NOT_IN_SUPPORTING"
            )
        target_id = state.pending_forced_swap_target_id
        if not target_id or target_id not in player.zones[Zone.ATTACKING.name].card_ids:
            return ValidationResult(
                valid=False, error="Forced swap target is invalid", error_code="INVALID_FORCED_SWAP_TARGET"
            )
        return ValidationResult(valid=True)

    def to_events(self, state: GameState) -> list[GameEvent]:
        if not state.pending_forced_swap_target_id:
            return []
        return [
            CardSwappedEvent(
                game_id=state.game_id,
                player_id=self.player_id,
                supporting_card_id=self.supporting_card_id,
                attacking_card_id=state.pending_forced_swap_target_id,
            )
        ]

    @classmethod
    def get_valid(cls, state: GameState, player_id: str) -> list[Action]:
        if state.pending_action != "forced_swap" or state.pending_defender_id != player_id:
            return []
        player = state.room.players.get(player_id)
        if not player:
            return []
        return [
            cls(player_id=player_id, supporting_card_id=cid)
            for cid in player.zones[Zone.SUPPORTING.name].card_ids
            if state.get_card(cid)
        ]


class ReviveFromGraveyardAction(Action):
    action_type: str = "revive_from_graveyard"
    valid_phases: list[TurnPhase] | None = [TurnPhase.ATTACK]
    source_card_id: str = ""
    graveyard_card_id: str = ""

    def validate(self, state: GameState) -> ValidationResult:
        from app.game.validators import ValidationResult

        player = state.room.get_player(self.player_id)
        source = state.get_card(self.source_card_id)
        target = state.get_card(self.graveyard_card_id)
        if not source or source.owner_id != self.player_id or source.zone not in (Zone.SUPPORTING, Zone.ATTACKING):
            return ValidationResult(valid=False, error="Invalid revive source", error_code="INVALID_REVIVE_SOURCE")
        if not can_revive_from_graveyard(state, source):
            return ValidationResult(
                valid=False, error="Card cannot revive from graveyard", error_code="REVIVE_NOT_ALLOWED"
            )
        if not target or self.graveyard_card_id not in player.zones[Zone.GRAVEYARD.name].card_ids:
            return ValidationResult(valid=False, error="Invalid graveyard card", error_code="INVALID_GRAVEYARD_CARD")
        return ValidationResult(valid=True)

    def to_events(self, state: GameState) -> list[GameEvent]:
        source = state.cards[self.source_card_id]
        return [
            CardRevivedEvent(
                game_id=state.game_id,
                player_id=self.player_id,
                source_card_id=self.source_card_id,
                revived_card_id=self.graveyard_card_id,
                target_zone=source.zone,
            )
        ]

    @classmethod
    def get_valid(cls, state: GameState, player_id: str) -> list[Action]:
        player = state.room.players[player_id]
        graveyard_ids = player.zones[Zone.GRAVEYARD.name].card_ids
        if not graveyard_ids:
            return []
        actions: list[Action] = []
        for source_id in player.get_active_cards():
            source = state.get_card(source_id)
            if source and can_revive_from_graveyard(state, source):
                for graveyard_id in graveyard_ids:
                    if state.get_card(graveyard_id):
                        actions.append(
                            cls(player_id=player_id, source_card_id=source_id, graveyard_card_id=graveyard_id)
                        )
        return actions
