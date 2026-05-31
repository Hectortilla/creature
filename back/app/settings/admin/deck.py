from sqladmin import ModelView

# Models
from app.models.db.deck import Deck


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
        "description": "Descripción",
        "deck_cards": "Cartas en el mazo",
        "user_id": "ID del Propietario",
    }
    column_details_list = [
        "id",
        "name",
        "user",
        "cards",
        "deck_cards",
        "description",
        "created_at",
    ]
    form_columns = [
        "id",
        "name",
        "user",
        "cards",
        "deck_cards",
        "description",
    ]
