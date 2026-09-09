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
    # Make name NOT NULL and remove username
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column(
            'name',
            existing_type=sa.String(length=80),
            nullable=False
        )
        batch_op.drop_column('username')


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('username', sa.String(length=80), nullable=True)
        )

    op.execute(
        'UPDATE users SET username = name'
    )

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column(
            'username',
            existing_type=sa.String(length=80),
            nullable=False
        )
        batch_op.drop_column('name')