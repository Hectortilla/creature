from sqladmin import ModelView
from wtforms import SelectField

from app.models.db.effect import Effect


class EffectAdmin(ModelView, model=Effect):
    name = "Efecto"
    name_plural = "Efectos"
    icon = "fa-solid fa-code-branch"
    category = "Motor de Juego"

    column_searchable_list = [
        Effect.owner_kind,
        Effect.atom_type,
        Effect.trigger,
        Effect.script_id,
        Effect.notes,
    ]
    column_sortable_list = [
        Effect.owner_kind,
        Effect.owner_id,
        Effect.atom_type,
        Effect.sort_order,
        Effect.enabled,
        Effect.created_at,
    ]
    column_default_sort = (Effect.owner_kind, False)

    column_list = [
        Effect.id,
        Effect.enabled,
        Effect.owner_kind,
        Effect.owner_id,
        Effect.atom_type,
        Effect.trigger,
        Effect.sort_order,
        Effect.script_id,
    ]

    column_details_list = [
        "id",
        "enabled",
        "owner_kind",
        "owner_id",
        "atom_type",
        "trigger",
        "params",
        "sort_order",
        "script_id",
        "notes",
        "created_at",
    ]

    form_columns = [
        "enabled",
        "owner_kind",
        "owner_id",
        "atom_type",
        "trigger",
        "params",
        "sort_order",
        "script_id",
        "notes",
    ]

    column_labels = {
        "id": "ID",
        "enabled": "Activo",
        "owner_kind": "Tipo de referencia",
        "owner_id": "ID de referencia",
        "atom_type": "Tipo de átomo",
        "trigger": "Disparador",
        "params": "Parámetros JSON",
        "sort_order": "Orden",
        "script_id": "Script registrado",
        "notes": "Notas",
        "created_at": "Creado el",
    }

    form_overrides = {
        "owner_kind": SelectField,
        "trigger": SelectField,
    }

    form_args = {
        "owner_kind": {
            "description": "Usa ability, attack o association.",
            "choices": [
                ("ability", "Habilidad"),
                ("attack", "Ataque"),
                ("association", "Asociación"),
            ],
        },
        "owner_id": {
            "description": "ID de la fila referenciada en abilities, attacks o associations.",
        },
        "atom_type": {
            "description": "Debe existir en EFFECT_REGISTRY.",
        },
        "trigger": {
            "description": "Opcional. Ej: ON_ATTACK_RESOLVE, ON_TAKE_DAMAGE, ON_ASSOCIATE.",
            "choices": [
                ("", "— Ninguno / pasivo —"),
                ("ON_ATTACK", "ON_ATTACK"),
                ("ON_DEFEND", "ON_DEFEND"),
                ("ON_DEAL_DAMAGE", "ON_DEAL_DAMAGE"),
                ("ON_TAKE_DAMAGE", "ON_TAKE_DAMAGE"),
                ("ON_ATTACK_RESOLVE", "ON_ATTACK_RESOLVE"),
                ("ON_ASSOCIATE", "ON_ASSOCIATE"),
                ("ON_ASSOCIATE_TARGET", "ON_ASSOCIATE_TARGET"),
                ("ON_ALLY_ATTACK", "ON_ALLY_ATTACK"),
                ("ON_TURN_START", "ON_TURN_START"),
                ("ON_TURN_END", "ON_TURN_END"),
            ],
        },
        "script_id": {
            "description": "Opcional. Solo scripts registrados, ej: cambio_de_guardia.",
        },
    }

    page_size = 50
    page_size_options = [25, 50, 100, 200]
