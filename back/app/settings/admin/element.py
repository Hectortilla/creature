from sqladmin import ModelView

# Models
from app.models.db.element import Element


class ElementAdmin(ModelView, model=Element):
    name = "Elemento"
    name_plural = "Elementos"
    icon = "fa-solid fa-fire"
    category = "Gestión de Cartas"

    searchable_columns = [Element.label]

    column_list = [
        Element.id,
        Element.label,
    ]
    column_labels = {
        "id": "ID",
        "label": "Label",
        "icon": "Icono",
        "color": "Color Hex",
        "strengths": "Fortalezas",
        "weaknesses": "Debilidades",
    }
    column_details_list = [
        "id",
        "label",
        "icon",
        "color",
        "strengths",
        "weaknesses",
    ]
    form_columns = [
        "label",
        "icon",
        "color",
        "strengths",
        "weaknesses",
    ]

    page_size = 20
