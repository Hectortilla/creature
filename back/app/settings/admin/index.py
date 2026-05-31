# app/settings/admin.py
from fastapi import FastAPI
from sqladmin import Admin

from app.database import engine

from .ability import AbilityAdmin
from .association import AssociationAdmin
from .attack import AttackAdmin
from .card import CardAdmin
from .character import CharacterAdmin
from .deck import DeckAdmin
from .effect import EffectAdmin
from .element import ElementAdmin
from .type import TypeAdmin

# Admins
from .user import UserAdmin


# --- Admin views ---
def setup_admin(app: FastAPI) -> None:
    """Init FastAPI Admin panel and register views."""

    admin = Admin(
        app,
        engine=engine,
        title="Alen Admin",
    )

    # Views registration
    admin.add_view(UserAdmin)
    admin.add_view(CardAdmin)
    admin.add_view(CharacterAdmin)
    admin.add_view(TypeAdmin)
    admin.add_view(ElementAdmin)
    admin.add_view(AttackAdmin)
    admin.add_view(AbilityAdmin)
    admin.add_view(AssociationAdmin)
    admin.add_view(EffectAdmin)
    admin.add_view(DeckAdmin)
