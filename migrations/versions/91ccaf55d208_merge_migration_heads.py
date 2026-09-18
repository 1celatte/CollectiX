"""Merge migration heads

Revision ID: 91ccaf55d208
Revises: 775ceaf41a8e, 081024102510
Create Date: 2026-09-10 19:42:19.118362

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '91ccaf55d208'
down_revision = ('775ceaf41a8e', '081024102510')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
