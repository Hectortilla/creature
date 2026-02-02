"""allow_repeated_cards_in_decks

Revision ID: allow_repeated_cards
Revises: c95fd519098c
Create Date: 2025-12-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'allow_repeated_cards'
down_revision: Union[str, None] = 'c95fd519098c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Allow cards to be repeated in decks by changing primary key structure."""
    # Drop the composite primary key
    op.drop_constraint('deck_cards_pkey', 'deck_cards', type_='primary')
    
    # Create sequence for id (PostgreSQL)
    op.execute("CREATE SEQUENCE IF NOT EXISTS deck_cards_id_seq")
    
    # Add id column (nullable first, we'll populate it then make it not null)
    op.add_column('deck_cards', sa.Column('id', sa.Integer(), nullable=True))
    
    # Populate id column with sequence values
    op.execute("""
        UPDATE deck_cards 
        SET id = nextval('deck_cards_id_seq')
    """)
    
    # Set sequence ownership and default
    op.execute("ALTER SEQUENCE deck_cards_id_seq OWNED BY deck_cards.id")
    op.alter_column('deck_cards', 'id', 
                    nullable=False,
                    server_default=sa.text("nextval('deck_cards_id_seq')"))
    
    # Set id as primary key
    op.create_primary_key('deck_cards_pkey', 'deck_cards', ['id'])
    
    # Add indexes on deck_id and card_id for better query performance
    op.create_index('ix_deck_cards_deck_id', 'deck_cards', ['deck_id'], unique=False)
    op.create_index('ix_deck_cards_card_id', 'deck_cards', ['card_id'], unique=False)


def downgrade() -> None:
    """Revert to composite primary key (no repeated cards)."""
    # Drop indexes
    op.drop_index('ix_deck_cards_card_id', table_name='deck_cards')
    op.drop_index('ix_deck_cards_deck_id', table_name='deck_cards')
    
    # Drop the id primary key
    op.drop_constraint('deck_cards_pkey', 'deck_cards', type_='primary')
    
    # Drop sequence
    op.execute("DROP SEQUENCE IF EXISTS deck_cards_id_seq")
    
    # Remove id column
    op.drop_column('deck_cards', 'id')
    
    # Restore composite primary key
    op.create_primary_key('deck_cards_pkey', 'deck_cards', ['deck_id', 'card_id'])

