"""
Combat actions (Attack, ForceDefend) and shared combat event generation.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from app.models.game.enums import Zone, TurnPhase
from app.models.game.events import (
    GameEvent,
    CardPromotedEvent,
    NoDefenderEvent,
    GameEndedEvent,
    ElementsConsumedEvent,
    AttackDeclaredEvent,
    DamageDealtEvent,
    CardDestroyedEvent,
)
from app.game.actions.base import Action
from app.game.elements import calculate_damage
from app.game.effects import get_passive_stat_modifiers

if TYPE_CHECKING:
    from app.models.game.state import GameState
    from app.models.game.card import GameCard
    from app.game.validators import ValidationResult


# ── Shared combat helper ────────────────────────────────────────────────

def build_combat_events(
    state: "GameState",
    attacker: "GameCard",
    target: "GameCard",
    attack,
    attacker_owner_id: str,
    consume_elements: bool = True,
) -> list[GameEvent]:
    """Build element-consumption + attack-declared + damage + destruction events."""
    events: list[GameEvent] = []

    if consume_elements:
        element_costs = {c.element_id: c.amount for c in attack.necessary_force}
        if element_costs:
            events.append(ElementsConsumedEvent(
                game_id=state.game_id, player_id=attacker_owner_id,
                elements=element_costs, for_attack_id=attack.attack_id,
            ))

    events.append(AttackDeclaredEvent(
        game_id=state.game_id, attacker_owner_id=attacker_owner_id,
        attacker_id=attacker.instance_id, target_id=target.instance_id,
        attack_id=attack.attack_id, attack_name=attack.name,
    ))

    attacker_mods = get_passive_stat_modifiers(state, attacker)
    target_mods = get_passive_stat_modifiers(state, target)
    effect_mod = attacker_mods["attack_bonus"] - target_mods["defense_bonus"]
    damage_calc = calculate_damage(attack, attacker, target, effect_modifier=effect_mod)

    if damage_calc.final_damage > 0:
        events.append(DamageDealtEvent(
            game_id=state.game_id, source_id=attacker.instance_id, target_id=target.instance_id,
            damage_type=attack.type, base_damage=damage_calc.base_damage,
            element_bonus=damage_calc.element_bonus, defense_reduction=damage_calc.defense_value,
            final_damage=damage_calc.final_damage,
            remaining_health=target.current_health - damage_calc.final_damage,
        ))
        if target.current_health - damage_calc.final_damage <= 0:
            events.append(CardDestroyedEvent(
                game_id=state.game_id, instance_id=target.instance_id,
                owner_id=target.owner_id, card_name=target.name, destroyed_by=attacker.instance_id,
            ))

    if damage_calc.reflected_damage > 0:
        events.append(DamageDealtEvent(
            game_id=state.game_id, source_id=target.instance_id, target_id=attacker.instance_id,
            damage_type=attack.type, base_damage=0, element_bonus=0, defense_reduction=0,
            final_damage=damage_calc.reflected_damage,
            remaining_health=attacker.current_health - damage_calc.reflected_damage,
        ))
        if attacker.current_health - damage_calc.reflected_damage <= 0:
            events.append(CardDestroyedEvent(
                game_id=state.game_id, instance_id=attacker.instance_id,
                owner_id=attacker.owner_id, card_name=attacker.name, destroyed_by=target.instance_id,
            ))

    return events


# ── Attack ──────────────────────────────────────────────────────────────

class AttackAction(Action):
    action_type: str = "attack"
    valid_phases: list[TurnPhase] | None = [TurnPhase.ATTACK]
    attacker_id: str = ""
    attack_id: int = 0
    target_card_id: str = ""

    def validate(self, state: "GameState") -> "ValidationResult":
        from app.game.validators import ValidationResult
        from app.game.elements import can_afford_attack
        player = state.room.get_player(self.player_id)
        opponent = state.room.get_opponent(self.player_id)
        if state.is_first_turn(self.player_id):
            return ValidationResult(valid=False, error="Cannot attack on first turn", error_code="FIRST_TURN_RESTRICTION")
        if self.attacker_id not in player.zones[Zone.ATTACKING.name].card_ids:
            return ValidationResult(valid=False, error="Attacker must be in attacking zone", error_code="ATTACKER_NOT_IN_ATTACKING")
        attacker = state.get_card(self.attacker_id)
        if not attacker or not attacker.can_attack:
            return ValidationResult(valid=False, error="Card cannot attack", error_code="CANNOT_ATTACK")
        attack = next((a for a in attacker.attacks if a.attack_id == self.attack_id), None)
        if not attack:
            return ValidationResult(valid=False, error="Card does not have this attack", error_code="INVALID_ATTACK")
        if not can_afford_attack({e: player.element_pool.get_available(e) for e in player.element_pool.elements}, attack):
            return ValidationResult(valid=False, error="Not enough elements", error_code="INSUFFICIENT_ELEMENTS")
        opponent_attacking = opponent.zones[Zone.ATTACKING.name]
        if self.target_card_id not in opponent_attacking.card_ids:
            if len(opponent_attacking.card_ids) == 0:
                return ValidationResult(valid=True)
            return ValidationResult(valid=False, error="Target must be in opponent's attacking zone", error_code="INVALID_TARGET")
        if not state.get_card(self.target_card_id):
            return ValidationResult(valid=False, error="Target card not found", error_code="TARGET_NOT_FOUND")
        return ValidationResult(valid=True)

    def to_events(self, state: "GameState") -> list[GameEvent]:
        opponent = state.room.get_opponent(self.player_id)
        attacker = state.get_card(self.attacker_id)
        if not attacker:
            return []
        attack = next((a for a in attacker.attacks if a.attack_id == self.attack_id), None)
        if not attack:
            return []

        if len(opponent.zones[Zone.ATTACKING.name].card_ids) == 0:
            if len(opponent.zones[Zone.SUPPORTING.name].card_ids) > 0:
                return [NoDefenderEvent(
                    game_id=state.game_id, defender_id=opponent.player_id, attacker_id=self.player_id,
                    must_defend=True, game_lost=False,
                    pending_attacker_card_id=self.attacker_id, pending_attack_id=self.attack_id,
                    pending_attacker_owner_id=self.player_id,
                )]
            else:
                return [
                    NoDefenderEvent(game_id=state.game_id, defender_id=opponent.player_id, attacker_id=self.player_id, must_defend=False, game_lost=True),
                    GameEndedEvent(game_id=state.game_id, winner_id=self.player_id, loser_id=opponent.player_id, reason="No defenders available"),
                ]

        target = state.get_card(self.target_card_id)
        if not target:
            return []
        return build_combat_events(state, attacker, target, attack, self.player_id)

    @classmethod
    def get_valid(cls, state: "GameState", player_id: str) -> list[Action]:
        if state.is_first_turn(player_id):
            return []
        player = state.room.players[player_id]
        opponent = next((p for pid, p in state.room.players.items() if pid != player_id), None)
        if not opponent:
            return []
        actions = []
        for attacker_id in player.zones[Zone.ATTACKING.name].card_ids:
            attacker = state.get_card(attacker_id)
            if not attacker or not attacker.can_attack:
                continue
            for attack in attacker.attacks:
                if not all(player.element_pool.get_available(c.element_id) >= c.amount for c in attack.necessary_force):
                    continue
                for target_id in opponent.zones[Zone.ATTACKING.name].card_ids:
                    actions.append(cls(player_id=player_id, attacker_id=attacker_id, attack_id=attack.attack_id, target_card_id=target_id))
                if len(opponent.zones[Zone.ATTACKING.name].card_ids) == 0:
                    actions.append(cls(player_id=player_id, attacker_id=attacker_id, attack_id=attack.attack_id, target_card_id=""))
        return actions


# ── Force Defend ────────────────────────────────────────────────────────

class ForceDefendAction(Action):
    action_type: str = "force_defend"
    valid_phases: list[TurnPhase] | None = [TurnPhase.ATTACK]
    instance_id: str = ""

    def validate(self, state: "GameState") -> "ValidationResult":
        from app.game.validators import ValidationResult
        if state.pending_action != "force_defend":
            return ValidationResult(valid=False, error="No force defend pending", error_code="NO_FORCE_DEFEND")
        player = state.room.get_player(self.player_id)
        if self.instance_id not in player.zones[Zone.SUPPORTING.name].card_ids:
            return ValidationResult(valid=False, error="Card must be in supporting zone", error_code="CARD_NOT_IN_SUPPORTING")
        if player.zones[Zone.ATTACKING.name].is_full:
            return ValidationResult(valid=False, error="Attacking zone is full", error_code="ATTACKING_ZONE_FULL")
        return ValidationResult(valid=True)

    def to_events(self, state: "GameState") -> list[GameEvent]:
        events = []
        card = state.get_card(self.instance_id)
        if card:
            events.append(CardPromotedEvent(
                game_id=state.game_id, player_id=self.player_id,
                instance_id=self.instance_id, card_id=card.card_id, card_name=card.name,
            ))
        if state.pending_attack and card:
            pending = state.pending_attack
            attacker = state.get_card(pending["attacker_id"])
            attack = next((a for a in attacker.attacks if a.attack_id == pending["attack_id"]), None) if attacker else None
            if attacker and attack:
                events.extend(build_combat_events(state, attacker, card, attack, pending["attacker_owner_id"]))
        return events

    @classmethod
    def get_valid(cls, state: "GameState", player_id: str) -> list[Action]:
        player = state.room.players.get(player_id)
        if not player:
            return []
        return [
            cls(player_id=player_id, instance_id=cid)
            for cid in player.zones[Zone.SUPPORTING.name].card_ids
            if state.get_card(cid)
        ]
