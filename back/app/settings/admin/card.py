from sqladmin import ModelView

# Models
from app.models.db.card import Card


class CardAdmin(ModelView, model=Card):
    name = "Carta"
    name_plural = "Cartas"
    icon = "fa-solid fa-id-badge"
    category = "Gestión de Cartas"

    searchable_columns = [Card.name]
    column_searchable_list = [Card.name, Card.code]

    column_list = [
        Card.id,
        Card.name,
        "character.label",
        "type.label",
        "first_element.label",
        "second_element",
    ]
    column_formatters = {
        "second_element": lambda model, a: model.second_element.label if model.second_element else "—",
        "first_element": lambda model, a: model.first_element.label,
    }
    column_details_list = [
        "id",
        "code",
        "image",
        "name",
        "description",
        "character",
        "type",
        "first_element",
        "second_element",
        "first_attack",
        "second_attack",
        "ability",
        "association",
        "is_evolution",
        "forces",
        "decks",
        "created_at",
    ]
    column_labels = {
        "id": "ID",
        "name": "Nombre",
        "character.label": "Naturaleza",
        "character": "Naturaleza",
        "type.label": "Tipo",
        "type": "Tipo",
        "first_attack": "Primer Ataque",
        "second_attack": "Segundo Ataque",
        "ability": "Habilidad",
        "association": "Asociacion",
        "is_evolution": "Evolucion",
        "forces": "Fuerzas",
        "decks": "Mazos",
        "created_at": "Creado el",
        "first_element.label": "Primer Elemento",
        "first_element": "Primer Elemento",
        "second_element": "Segundo Elemento",
        "physical_defence": "Defensa Física",
        "magic_defence": "Defensa Mágica",
        "description": "Descripción",
        "health": "Vida",
        "damage": "Daño",
        "image": "Imagen",
        "is_evolution_id": "Evoluciona de (ID)",
        "handle": "Handle",
        "code": "Código",
        "first_attack_id": "Primer Ataque (ID)",
        "second_attack_id": "Segundo Ataque (ID)",
        "ability_id": "Habilidad (ID)",
        "association_id": "Asociacion (ID)",
        "character_id": "Naturaleza (ID)",
        "type_id": "Tipo (ID)",
        "first_element_id": "Primer Elemento (ID)",
        "second_element_id": "Segundo Elemento (ID)",
    }

    form_labels = {
        "id": "ID",
        "name": "Nombre",
        "character.label": "Naturaleza",
        "type.label": "Tipo",
        "first_element.label": "Primer Elemento",
    }

    form_columns = [
        "id",
        "code",
        "image",
        "name",
        "description",
        "character",
        "type",
        "first_element",
        "second_element",
        "first_attack",
        "second_attack",
        "ability",
        "association",
        "is_evolution",
        "forces",
        "decks",
        "created_at",
    ]

    form_args = {
        "type": {
            "get_label": lambda obj: obj.label if hasattr(obj, "label") else str(obj),
            "allow_blank": False,
            "blank_text": "— Selecciona un elemento —",
        },
        "character": {
            "get_label": lambda obj: obj.label if hasattr(obj, "label") else str(obj),
            "allow_blank": False,
            "blank_text": "— Selecciona una naturaleza —",
        },
        "first_element": {
            "get_label": lambda obj: obj.label if hasattr(obj, "label") else str(obj),
            "allow_blank": False,
            "blank_text": "— Selecciona un elemento —",
        },
        "second_element": {
            "get_label": lambda obj: obj.label if hasattr(obj, "label") else str(obj),
            "allow_blank": False,
            "blank_text": "— Selecciona un elemento —",
        },
        "first_attack": {
            "get_label": lambda obj: obj.name if hasattr(obj, "name") else str(obj),
            "allow_blank": False,
            "blank_text": "— Selecciona un ataque —",
        },
        "second_attack": {
            "get_label": lambda obj: obj.name if hasattr(obj, "name") else str(obj),
            "allow_blank": False,
            "blank_text": "— Selecciona un ataque —",
        },
        "ability": {
            "get_label": lambda obj: obj.name if hasattr(obj, "name") else str(obj),
            "allow_blank": False,
            "blank_text": "— Selecciona una habilidad —",
        },
        "association": {
            "get_label": lambda obj: obj.name if hasattr(obj, "name") else str(obj),
            "allow_blank": False,
            "blank_text": "— Selecciona una asociación —",
        },
        "is_evolution": {
            "get_label": lambda obj: obj.name if hasattr(obj, "name") else str(obj),
            "allow_blank": False,
            "blank_text": "— Selecciona una evolución —",
        },
    }

    column_default_sort = (Card.name, False)
    searchable_columns = [Card.name]

    page_size = 50
    page_size_options = [25, 50, 100, 200]

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
