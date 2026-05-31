from sqladmin import ModelView

# Models
from app.models.db.character import Character


class CharacterAdmin(ModelView, model=Character):
    name = "Naturaleza"
    name_plural = "Naturalezas"
    icon = "fa-solid fa-leaf"
    category = "Gestión de Cartas"

    searchable_columns = [Character.label]

    column_list = [
        Character.id,
        Character.label,
    ]
    column_labels = {
        "id": "ID",
        "label": "Label",
        "icon": "Icono",
    }
    column_details_list = [
        "id",
        "label",
        "icon",
    ]
    form_columns = [
        "label",
        "icon",
    ]

    page_size = 20
