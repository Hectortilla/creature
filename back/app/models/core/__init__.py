"""
Core Field Definitions

Pure Pydantic classes that define shared fields between:
- Base models (SQLModel for DB)
- Game models (Pydantic for runtime)
- Schema models (Pydantic for API)

These are designed as mixins/base classes that can be inherited by both
SQLModel and Pydantic models without conflict.
"""

from app.models.core.card import CardCombatFields, CardIdentityFields
from app.models.core.attack import AttackCoreFields


