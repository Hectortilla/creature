"""merge user_cards and effects branches

Revision ID: 004_merge
Revises: 4588442c7050, 003_effects
Create Date: 2026-05-31

"""

from collections.abc import Sequence
from typing import Union

revision: str = "004_merge"
down_revision: str | Sequence[str] | None = ("4588442c7050", "003_effects")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
