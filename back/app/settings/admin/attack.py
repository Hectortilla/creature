from sqladmin import ModelView

# Models
from app.models.db.attack import Attack


class AttackAdmin(ModelView, model=Attack):
    name = "Ataque"
    name_plural = "Ataques"
    icon = "fa-solid fa-bolt"
    category = "Gestión de Cartas"

    searchable_columns = [Attack.name]
    
    
    column_list = [
        Attack.id,
        Attack.name,
        Attack.damage,
        "element.label",
    ]
    column_labels = {
        "id": "ID",
        "name": "Nombre",
        "damage": "Daño",
        "element.label": "Elemento",
        "element": "Elemento",
        "element_id": "Elemento (ID)",
        "description": "Descripción",
        "effect": "Efecto",
        "dice_rolls": "Tiradas de Dado",
        "type": "Tipo",
        "code": "Código",
        "handle": "Handle",
        "necessary_force": "Fuerza Necesaria",
        "created_at": "Creado el",
    }
    
    column_details_list = [
        "id",
        "name",
        "damage",
        "element",
        "element_id",
        "description",
        "effect",
        "dice_rolls",
        "type",
        "code",
        "handle",
        "necessary_force",
        "created_at",
    ]
    
    form_columns = [
        "id",
        "name",
        "damage",
        "element",
        "description",
        "effect",
        "dice_rolls",
        "type",
        "code",
        "handle",
        "necessary_force",
    ]
    
    column_formatters = {
        "element": lambda model, a: model.element.label,
    }
    
    page_size = 50
    page_size_options = [25, 50, 100, 200]
