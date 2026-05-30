"""data driven effects

Revision ID: 003_effects
Revises: allow_repeated_cards
Create Date: 2026-05-23

"""
from typing import Sequence, Union
import json

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "003_effects"
down_revision: Union[str, None] = "allow_repeated_cards"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


OWNER_TABLES = {
    "ability": "abilities",
    "attack": "attacks",
    "association": "associations",
}


def _insert(conn, owner_kind: str, owner_handle: str, atom_type: str, params: dict,
            sort_order: int = 0, trigger: str | None = None, script_id: str | None = None,
            notes: str | None = None) -> None:
    table = OWNER_TABLES[owner_kind]
    conn.execute(sa.text(f"""
        INSERT INTO effects (owner_kind, owner_id, atom_type, trigger, params, sort_order, script_id, enabled, notes, created_at)
        SELECT :owner_kind, id, :atom_type, :trigger, CAST(:params AS JSONB), :sort_order, :script_id, TRUE, :notes, NOW()
        FROM {table}
        WHERE handle = :owner_handle
    """), {
        "owner_kind": owner_kind,
        "owner_handle": owner_handle,
        "atom_type": atom_type,
        "trigger": trigger,
        "params": json.dumps(params),
        "sort_order": sort_order,
        "script_id": script_id,
        "notes": notes,
    })


def upgrade() -> None:
    op.create_table(
        "effects",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("owner_kind", sa.String(length=32), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("atom_type", sa.String(length=128), nullable=False),
        sa.Column("trigger", sa.String(length=64), nullable=True),
        sa.Column("params", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("script_id", sa.String(length=128), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_effects_owner_kind", "effects", ["owner_kind"])
    op.create_index("ix_effects_owner_id", "effects", ["owner_id"])
    op.create_index("ix_effects_atom_type", "effects", ["atom_type"])
    op.create_index("ix_effects_owner", "effects", ["owner_kind", "owner_id"])

    conn = op.get_bind()

    # Abilities
    _insert(conn, "ability", "sequedad", "incoming-damage-modifier", {"scope": "self", "attack_element_id": 3, "delta": 10}, 1)
    _insert(conn, "ability", "sequedad", "incoming-damage-modifier", {"scope": "self", "attack_element_id": 2, "delta": -10}, 2)
    _insert(conn, "ability", "esqueje", "stat-modifier", {"scope": "allies_active", "filter_element_id": 9, "health": 10, "attack": 10})
    _insert(conn, "ability", "paz-mental", "immunity", {"scope": "allies_active", "filter_element_id": 11, "immune_kind": "magical_negative"})
    _insert(conn, "ability", "proteico", "stat-modifier", {"scope": "allies_active", "damage_type": "physical", "attack": 10})
    _insert(conn, "ability", "contemporizar", "ally-attack-rider", {"fraction": 0.3333333333, "attack_index": 0}, trigger="ON_ALLY_ATTACK")
    _insert(conn, "ability", "escudo", "stat-modifier", {"scope": "allies_active", "damage_type": "physical", "defense": 10})
    _insert(conn, "ability", "sacrificio", "rule-modifier", {"scope": "self", "can_revive_from_graveyard": True})
    _insert(conn, "ability", "control-total-sobre-la-magia", "immunity", {"scope": "self", "enemy_damage_type": "magical"})
    _insert(conn, "ability", "control-total-sobre-la-magia", "immunity", {"scope": "self", "immune_kind": "magical_negative"}, 2)
    _insert(conn, "ability", "individualista", "rule-modifier", {"scope": "self", "associations_allowed": False})
    _insert(conn, "ability", "trabajo-en-equipo", "rule-modifier", {"scope": "self", "max_associations": 2})
    _insert(conn, "ability", "piel-ardiente", "on-take-damage-punish", {"exclude_attacker_element_id": 5, "attacker_health_delta": -10}, trigger="ON_TAKE_DAMAGE")
    _insert(conn, "ability", "bajo-cero", "on-take-damage-status", {"exclude_attacker_element_id": 6, "status_type": "BLOCK_ATTACK", "duration_turns": 1}, trigger="ON_TAKE_DAMAGE")
    _insert(conn, "ability", "estatica", "on-take-damage-status", {"exclude_attacker_element_ids": [7, 2], "status_type": "BLOCK_ATTACK", "duration_turns": 1}, trigger="ON_TAKE_DAMAGE")
    _insert(conn, "ability", "intangible", "immunity", {"scope": "self", "enemy_damage_type": "physical"})
    _insert(conn, "ability", "intangible", "immunity", {"scope": "self", "immune_kind": "physical_negative"}, 2)
    _insert(conn, "ability", "luna-de-sangre", "stat-modifier", {"scope": "self", "damage_types": ["physical", "magical"], "multiplier": 2, "every_n_turns": 3})
    _insert(conn, "ability", "hijas-de-nix", "stat-modifier-per-named-card", {"scope": "allies_active", "damage_type": "magical", "defense_per": 20, "character_name": "Moira"})
    _insert(conn, "ability", "nevada", "stat-modifier", {"scope": "allies_active", "filter_element_id": 6, "damage_types": ["physical", "magical"], "attack": 20})
    _insert(conn, "ability", "sofoco", "stat-modifier", {"scope": "allies_active", "filter_element_id": 5, "damage_types": ["physical", "magical"], "attack": 20})

    # Attacks
    _insert(conn, "attack", "chispa-colateral", "splash-adjacent", {"fraction": 0.5, "exclude_target_element_id": 7}, trigger="ON_ATTACK_RESOLVE")
    _insert(conn, "attack", "agarre", "apply-status", {"dice_face": 3, "status_type": "DICE_LOCKED_ATTACK", "duration_turns": 1, "required_face": 3, "purpose": "dice_lock_next_attack"}, trigger="ON_ATTACK_RESOLVE")
    _insert(conn, "attack", "eco", "multi-target-zone", {"scope": "all_enemy_attacking"})
    _insert(conn, "attack", "brasas", "damage-over-time", {"amount": 10, "duration_turns": 2, "immune_element_id": 5}, trigger="ON_ATTACK_RESOLVE")
    _insert(conn, "attack", "escarcha", "damage-over-time", {"amount": 10, "duration_turns": 2, "immune_element_id": 6}, trigger="ON_ATTACK_RESOLVE")
    _insert(conn, "attack", "absorber-energia", "self-heal-scaled", {"base_heal": 10, "bonus_heal": 10, "bonus_target_element_ids": [3, 12]}, trigger="ON_ATTACK_RESOLVE")
    _insert(conn, "attack", "explosion-electrica", "apply-status", {"dice_face": 3, "status_type": "BLOCK_ATTACK", "duration_turns": 1, "purpose": "dice_block_attack"}, trigger="ON_ATTACK_RESOLVE")
    _insert(conn, "attack", "vendaval-", "force-swap-on-high-damage", {"threshold": 100}, trigger="ON_ATTACK_RESOLVE")
    _insert(conn, "attack", "bola-de-nieve", "attack-cooldown", {"scope": "self", "attack_cooldown_turns": 1})
    _insert(conn, "attack", "roce-toxico", "damage-over-time", {"amount": 10, "duration_turns": 2, "immune_element_id": 10}, trigger="ON_ATTACK_RESOLVE")
    _insert(conn, "attack", "vomito", "self-damage", {"amount": 10}, trigger="ON_ATTACK_RESOLVE")
    _insert(conn, "attack", "invocacion", "exile-graveyard-ally-cost", {"exclude_element_id": 13})

    # Associations
    _insert(conn, "association", "buena-suerte", "association-target-filter", {"target_filter_type_id": 6}, 1)
    _insert(conn, "association", "buena-suerte", "stat-modifier", {"scope": "host", "damage_type": "magical", "defense": 20}, 2)
    _insert(conn, "association", "cambio-de-guardia", "script", {"playable_directly_from_hand": True}, trigger="ON_ASSOCIATE", script_id="cambio_de_guardia")
    _insert(conn, "association", "brote", "association-target-filter", {"target_filter_element_id": 9}, 1)
    _insert(conn, "association", "brote", "stat-modifier", {"scope": "host", "attack": 20, "health": 20}, 2)
    _insert(conn, "association", "maldicion-del-alma-perdida", "stat-modifier", {"scope": "host", "defense_override": 0, "attack": 40}, 1)
    _insert(conn, "association", "maldicion-del-alma-perdida", "damage-over-time", {"amount": 10, "duration_turns": -1, "delay_turns": 1}, 2, trigger="ON_ASSOCIATE_TARGET")
    _insert(conn, "association", "proteina", "stat-modifier", {"scope": "host", "damage_type": "physical", "attack": 20})
    _insert(conn, "association", "mutacion-x", "association-target-filter", {"target_filter_type_id": 4}, 1)
    _insert(conn, "association", "mutacion-x", "stat-modifier", {"scope": "host", "damage_types": ["physical", "magical"], "attack": 20}, 2)
    _insert(conn, "association", "pocion", "on-associate-grant-then-exile", {"health": 20, "exile_trigger": "host_first_attack"}, trigger="ON_ASSOCIATE")


def downgrade() -> None:
    op.drop_index("ix_effects_owner", table_name="effects")
    op.drop_index("ix_effects_atom_type", table_name="effects")
    op.drop_index("ix_effects_owner_id", table_name="effects")
    op.drop_index("ix_effects_owner_kind", table_name="effects")
    op.drop_table("effects")
