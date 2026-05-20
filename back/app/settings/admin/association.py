from sqladmin import ModelView

# Models
from app.models.db.association import Association


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
        "description": "Descripción",
        "code": "Código",
        "handle": "Handle",
        "created_at": "Creado el",
    }
    column_details_list = [
        "id",
        "name",
        "description",
        "code",
        "handle",
        "created_at",
    ]
    form_columns = [
        "name",
        "description",
        "code",
        "handle",
    ]
    
    page_size = 50
    page_size_options = [25, 50, 100, 200]