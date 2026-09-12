"""Remove username and add name

Revision ID: d957f9d05c8e
Revises: bf0b9aac52a9
Create Date: 2026-09-05 14:19:24.343636
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd957f9d05c8e'
down_revision = 'bf0b9aac52a9'
branch_labels = None
depends_on = None


def upgrade():
    # Add name temporarily so existing username data can be preserved.
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('name', sa.String(length=80), nullable=True)
        )

    # Copy existing usernames into the new name column.
    op.execute(
        'UPDATE users SET name = username'
    )

    # Make name required and remove the old username column.
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column(
            'name',
            existing_type=sa.String(length=80),
            nullable=False
        )
        batch_op.drop_column('username')


def downgrade():
    # Restore username temporarily as nullable.
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('username', sa.String(length=80), nullable=True)
        )

    # Copy names back into username.
    op.execute(
        'UPDATE users SET username = name'
    )

    # Make username required and remove name.
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column(
            'username',
            existing_type=sa.String(length=80),
            nullable=False
        )
        batch_op.drop_column('name')