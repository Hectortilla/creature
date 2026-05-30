# app/settings/admin.py
from sqladmin import Admin
from fastapi import FastAPI
from app.database import engine


# Admins
from .user import UserAdmin
from .card import CardAdmin
from .character import CharacterAdmin
from .type import TypeAdmin
from .element import ElementAdmin
from .attack import AttackAdmin
from .ability import AbilityAdmin
from .association import AssociationAdmin
from .effect import EffectAdmin
from .deck import DeckAdmin


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
