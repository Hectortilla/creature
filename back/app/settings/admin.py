# app/settings/admin.py
from markupsafe import Markup
from sqladmin import Admin, ModelView
from fastapi import FastAPI
from app.database import engine
from wtforms.widgets import ColorInput
from wtforms.fields import ColorField, StringField

# Models
from app.models.db.user import User
from app.models.db.card import Card
from app.models.db.type import Type
from app.models.db.character import Character
from app.models.db.element import Element
from app.models.db.association import Association
from app.models.db.attack import Attack
from app.models.db.ability import Ability
from app.models.db.deck import Deck

# --- Admin views ---
class UserAdmin(ModelView, model=User):
    name = "Usuario"
    name_plural = "Usuarios"
    icon = "fa-solid fa-user"
    category = "Gestión de Cuentas"
    
    column_list = [User.id, User.username, User.email, User.disabled]
    column_default_sort = (User.username, False)
    searchable_columns = [User.username, User.email]
    
    searchable_columns = [User.username, User.email]
    icon = "fa-solid fa-user"
    
    page_size = 50
    page_size_options = [25, 50, 100, 200]
    
    form_excluded_columns = [User.hashed_password]
    form_read_only_columns = [User.id, User.created_at]
    
    form_labels = {
        "username": "Nombre de Usuario",
        "email": "Correo Electrónico",
        "disabled": "¿Cuenta Activa?"
    }
    
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True



class CardAdmin(ModelView, model=Card):
    name = "Carta"
    name_plural = "Cartas"
    icon = "fa-solid fa-id-badge"
    category = "Gestión de Cartas"

    searchable_columns = [Card.name]
    
    column_list = [
        Card.id,
        Card.name,
        "character.label",
        "type.label",
        "first_element.label",
        "second_element",
    ]
    column_formatters = {
        # Validamos: si existe 'second_element', saca su label. Si es None, pone un guión.
        "second_element": lambda model, a: (
            model.second_element.label 
            if model.second_element 
            else "—"
        ),
        "first_element": lambda model, a: model.first_element.label,
    }
    column_details_list = [
        "id",
        "code",
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
        "is_evolution": "Evoluciona de",
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
        "first_element.label": "Primer Elemento"
    }
    
    form_columns = [
        "id",
        "code",
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
            "blank_text": "— Selecciona un elemento —"
        },
        "character": {
            "get_label": lambda obj: obj.label if hasattr(obj, "label") else str(obj),
            "allow_blank": False,
            "blank_text": "— Selecciona una naturaleza —"
        },
        "first_element": {
            "get_label": lambda obj: obj.label if hasattr(obj, "label") else str(obj),
            "allow_blank": False,
            "blank_text": "— Selecciona un elemento —"
        },
        "second_element": {
            "get_label": lambda obj: obj.label if hasattr(obj, "label") else str(obj),
            "allow_blank": False,
            "blank_text": "— Selecciona un elemento —"
        },
        "first_attack": {
            "get_label": lambda obj: obj.name if hasattr(obj, "name") else str(obj),
            "allow_blank": False,
            "blank_text": "— Selecciona un ataque —"
        },
        "second_attack": {
            "get_label": lambda obj: obj.name if hasattr(obj, "name") else str(obj),
            "allow_blank": False,
            "blank_text": "— Selecciona un ataque —"
        },
        "ability": {
            "get_label": lambda obj: obj.name if hasattr(obj, "name") else str(obj),
            "allow_blank": False,
            "blank_text": "— Selecciona una habilidad —"
        },
        "association": {
            "get_label": lambda obj: obj.name if hasattr(obj, "name") else str(obj),
            "allow_blank": False,
            "blank_text": "— Selecciona una asociación —"
        },
        "is_evolution": {
            "get_label": lambda obj: obj.name if hasattr(obj, "name") else str(obj),
            "allow_blank": False,
            "blank_text": "— Selecciona una evolución —"
        }
    }
    
    column_default_sort = (Card.name, False)
    searchable_columns = [Card.name]
    
    
    page_size = 50
    page_size_options = [25, 50, 100, 200]
    

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    
    
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
    

class ElementAdmin(ModelView, model=Element):
    name = "Elemento"
    name_plural = "Elementos"
    icon = "fa-solid fa-fire"
    category = "Gestión de Cartas"

    searchable_columns = [Element.label]
    
    column_list = [
        Element.id,
        Element.label,
        "color_preview",
    ]
    column_labels = {
        "id": "ID",
        "label": "Label",
        "icon": "Icono",
        "color": "Color Hex",
        "color_preview": "Color",
        "strengths": "Fortalezas",
        "weaknesses": "Debilidades",
    }
    column_details_list = [
        "id",
        "label",
        "icon",
        "color",
        "color_preview",
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
    
    # 1. 🔥 Forzamos el campo 'color' para que sea un StringField en WTForms
    form_overrides = {
        "color": ColorField,
    }

    # 2. 🎨 Le inyectamos el Widget de paleta de colores nativa de HTML
    form_args = {
        "color": {
            "default": "#ffffff"
        }
    }

    # 3. 👁️ Formateador para ver el círculo con el color real en la tabla y detalles
    column_formatters = {
        "color_preview": lambda model, a: Markup(
            f'<div style="background-color: {model.color}; width: 24px; height: 24px; border-radius: 50%; border: 1px solid #ccc; display: inline-block; vertical-align: middle;"></div>'
        ) if model.color else "—",
    }
    
    

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
        "element.label": "Elemento"
    }
    
    column_formatters = {
        # Extraemos de forma segura el label a través de la relación si existe
        "element": lambda model, a: model.element.label,
    }
    
    page_size = 50
    page_size_options = [25, 50, 100, 200]
    
    
    
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
        "type": "Tipo"
    }
    
    page_size = 50
    page_size_options = [25, 50, 100, 200]
    
    
class AssociationAdmin(ModelView, model=Association):
    name = "Asociacion"
    name_plural = "Asociaciones"
    icon = "fa-solid fa-link"
    category = "Gestión de Cartas"

    searchable_columns = [Association.name]
    
    column_list = [
        Association.id,
        Association.name,
    ]
    
    column_labels = {
        "id": "ID",
        "name": "Nombre",
    }
    
    page_size = 50
    page_size_options = [25, 50, 100, 200]


class DeckAdmin(ModelView, model=Deck):
    name = "Mazo"
    name_plural = "Mazos"
    icon = "fa-solid fa-layer-group"
    category = "Gestión de Mazos"
    
    column_list = [Deck.id, Deck.name, Deck.user]
    column_default_sort = (Deck.name, False)

    searchable_columns = [Deck.name]
    
    column_labels = {
        "id": "ID",
        "name": "Nombre",
        "user": "Propietario",
        "cards": "Cartas",
        "created_at": "Creado el",
        "updated_at": "Actualizado el",
        "description": "Descripción",
    }


# --- Init ---
def setup_admin(app: FastAPI) -> None:
    """Init FastAPI Admin panel and register views."""
    admin = Admin(app, engine)
    
    # Views registration
    admin.add_view(UserAdmin)
    admin.add_view(CardAdmin)
    admin.add_view(CharacterAdmin)
    admin.add_view(TypeAdmin)
    admin.add_view(ElementAdmin)
    admin.add_view(AttackAdmin)
    admin.add_view(AbilityAdmin)
    admin.add_view(AssociationAdmin)
    admin.add_view(DeckAdmin)
    
    
    
    
    
    
# DOCS:
# ==========================================
# 1. IDENTIDAD Y MENÚ
# ==========================================
### name = "Usuario"                # Nombre en singular dentro del admin
### name_plural = "Usuarios"        # Nombre en plural para los menús
### icon = "fa-solid fa-user"       # Icono de FontAwesome (v6)
### category = "Gestión de Cuentas" # Agrupa varios modelos en un desplegable lateral

# ==========================================
# 2. VISTA DE LISTA (TABLA MAIN)
# ==========================================
# Columnas que se mostrarán en la tabla principal
### column_list = [User.id, User.username, User.email, User.is_active]

# Columnas que se pueden ordenar haciendo clic en el encabezado
### column_sortable_list = [User.id, User.username]

# Columna por la que se ordena por defecto (True = Descendiente, False = Ascendiente)
### column_default_sort = (User.id, True) 

# Habilitar barra de búsqueda (Soporta strings o atributos de SQLAlchemy)
### searchable_columns = [User.username, User.email]

# Elementos por página en la paginación
### page_size = 50
### page_size_options = [25, 50, 100, 200]

# ==========================================
# 3. FILTROS (El que causaba el error)
# ==========================================
# SQLAdmin mapea esto internamente. Si usas SQLAlchemy 2.0 moderno (con Mapped),
# y te da error de 'parameter_name', utiliza la propiedad literal en string.
### column_filters = ["email", "is_active"]

# ==========================================
# 4. FORMULARIOS (CREAR / EDITAR)
# ==========================================
# Campos que aparecerán en el formulario de creación/edición
### form_columns = [User.username, User.email, User.password, User.is_active]

# Campos que se excluyen del formulario
### form_excluded_columns = [User.hashed_password]

# Volver ciertos campos de "Solo lectura" en el formulario
### form_read_only_columns = [User.id]

# Cambiar las etiquetas (labels) que ve el usuario en los formularios
### form_labels = {
    ### "username": "Nombre de Usuario",
    ### "email": "Correo Electrónico",
    ### "is_active": "¿Cuenta Activa?"
### }

# Descripciones o textos de ayuda debajo de los inputs
### form_args = {
    ### "username": {
        ### "description": "El nombre debe ser único y no contener espacios."
    ### }
### }

# ==========================================
# 5. DETALLES (VISTA DEL OJO 👁️)
# ==========================================
# Columnas que se muestran al entrar a ver el detalle de un registro específico
### column_details_list = [User.id, User.username, User.email, User.created_at]

# ==========================================
# 6. CONTROL DE PERMISOS / ACCIONES
# ==========================================
### can_create = True    # ¿Se pueden crear nuevos registros?
### can_edit = True      # ¿Se pueden editar?
### can_delete = False   # ¿Se pueden borrar? (Útil para evitar desastres en producción)
### can_view_details = True # ¿Se puede ver la pestaña de detalles?

# ==========================================
# 7. FORMATEADORES AVANZADOS (HTML en celdas)
# ==========================================
# Puedes interceptar cómo se pinta una celda en la tabla. 
# Por ejemplo, pintar el email en negrita o agregar un badge de color:
### column_formatters = {
    ### User.email: lambda model, attribute: f"📧 {model.email}",
    ### User.is_active: lambda model, attribute: Markup(
        ### '<span class="badge bg-success">Activo</span>' if model.is_active 
        ### else '<span class="badge bg-danger">Inactivo</span>'
    ### )
### }