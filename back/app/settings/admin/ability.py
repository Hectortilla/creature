from sqladmin import ModelView

# Models
from app.models.db.ability import Ability
from app.settings.admin.effect_display import effect_summary


class AbilityAdmin(ModelView, model=Ability):
    name = "Habilidad"
    name_plural = "Habilidades"
    icon = "fa-solid fa-shield-alt"
    category = "Gestión de Cartas"

    searchable_columns = [Ability.name]

    column_list = [
        Ability.id,
        Ability.name,
        Ability.type,
    ]
    column_labels = {
        "id": "ID",
        "name": "Nombre",
        "description": "Descripción",
        "code": "Código",
        "handle": "Handle",
        "type": "Tipo",
        "created_at": "Creado el",
        "effect_summary": "Efectos",
    }
    column_details_list = [
        "id",
        "name",
        "description",
        "code",
        "type",
        "handle",
        "effect_summary",
        "created_at",
    ]
    column_formatters_detail = {
        "effect_summary": lambda model, a: effect_summary("ability", model.id),
    }
    form_columns = [
        "name",
        "description",
        "type",
        "code",
        "handle",
    ]

    page_size = 50
    page_size_options = [25, 50, 100, 200]
