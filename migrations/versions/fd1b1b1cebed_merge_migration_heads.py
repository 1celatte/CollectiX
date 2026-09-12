"""merge migration heads

Revision ID: fd1b1b1cebed
Revises: 7cc3a283cc36, 931728661754
Create Date: 2026-09-12 22:11:58.020980

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fd1b1b1cebed'
down_revision = ('7cc3a283cc36', '931728661754')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
