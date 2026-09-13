"""Merge migration heads

Revision ID: 57d582ec9efc
Revises: 91ccaf55d208, fd1b1b1cebed
Create Date: 2026-09-13 22:44:27.529998

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '57d582ec9efc'
down_revision = ('91ccaf55d208', 'fd1b1b1cebed')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
