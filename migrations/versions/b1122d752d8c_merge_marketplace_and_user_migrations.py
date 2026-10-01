"""Merge marketplace and user migrations

Revision ID: b1122d752d8c
Revises: 057294278e8d, 0e584b83d89b
Create Date: 2026-09-23 22:01:20.227985

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b1122d752d8c'
down_revision = ('057294278e8d', '0e584b83d89b')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
