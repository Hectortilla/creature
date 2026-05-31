from sqladmin import ModelView

# Models
from app.models.db.user import User


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

    form_read_only_columns = [User.id, User.created_at]

    form_labels = {
        "username": "Nombre de Usuario",
        "email": "Correo Electrónico",
        "disabled": "¿Cuenta Activa?",
        "cards": "Cartas del Usuario",
        "decks": "Mazos del Usuario",
    }

    column_details_list = ["id", "username", "email", "disabled", "cards", "decks", "created_at"]

    column_labels = {
        "id": "ID",
        "username": "Nombre de Usuario",
        "email": "Correo Electrónico",
        "disabled": "¿Cuenta Desactivada?",
        "created_at": "Creado el",
        "cards": "Cartas del Usuario",
        "decks": "Mazos del Usuario",
    }

    form_columns = ["id", "username", "email", "disabled", "cards", "decks", "created_at"]

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
