from sqladmin import ModelView

# Models
from app.models.db.type import Type


class TypeAdmin(ModelView, model=Type):
    name = "Tipo"
    name_plural = "Tipos"
    icon = "fa-solid fa-crow"
    category = "Gestión de Cartas"

    searchable_columns = [Type.label]

    column_list = [
        Type.id,
        Type.label,
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
