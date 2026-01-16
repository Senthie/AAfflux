"""update_node_model_remove_name_rename_position_to_ui

Revision ID: 89a90219e9f3
Revises: 8ea0549bc3e0
Create Date: 2026-01-16 16:19:25.512045

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '89a90219e9f3'
down_revision: Union[str, Sequence[str], None] = '8ea0549bc3e0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Rename 'position' column to 'ui'
    op.alter_column('nodes', 'position', new_column_name='ui')

    # Drop 'name' column
    op.drop_column('nodes', 'name')


def downgrade() -> None:
    """Downgrade schema."""
    # Add 'name' column back
    op.add_column('nodes', sa.Column('name', sa.String(length=255), nullable=True))

    # Rename 'ui' column back to 'position'
    op.alter_column('nodes', 'ui', new_column_name='position')
