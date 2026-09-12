"""add normalized names

Revision ID: 7cc3a283cc36
Revises: 081024102510
Create Date: 2026-09-12 00:05:14.075780
"""

from alembic import op
import sqlalchemy as sa
import unicodedata


# revision identifiers, used by Alembic.
revision = "7cc3a283cc36"
down_revision = "081024102510"
branch_labels = None
depends_on = None


def normalize_text(text):
    text = text or ""
    text = text.strip()

    normalized = unicodedata.normalize("NFKD", text)

    return "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    ).casefold()


def upgrade():
    # ----------------------------------------------------------
    # 1. Add normalized_name columns temporarily as nullable.
    # ----------------------------------------------------------

    with op.batch_alter_table(
        "tags",
        schema=None
    ) as batch_op:
        batch_op.add_column(
            sa.Column(
                "normalized_name",
                sa.String(length=80),
                nullable=True
            )
        )

    with op.batch_alter_table(
        "collections",
        schema=None
    ) as batch_op:
        batch_op.add_column(
            sa.Column(
                "normalized_name",
                sa.String(length=150),
                nullable=True
            )
        )

    with op.batch_alter_table(
        "items",
        schema=None
    ) as batch_op:
        batch_op.add_column(
            sa.Column(
                "normalized_name",
                sa.String(length=150),
                nullable=True
            )
        )

    # ----------------------------------------------------------
    # 2. Backfill existing Tag names.
    # ----------------------------------------------------------

    connection = op.get_bind()

    tags = connection.execute(
        sa.text(
            "SELECT id, name FROM tags"
        )
    ).fetchall()

    for tag in tags:
        connection.execute(
            sa.text(
                """
                UPDATE tags
                SET normalized_name = :normalized_name
                WHERE id = :id
                """
            ),
            {
                "id": tag.id,
                "normalized_name": normalize_text(tag.name)
            }
        )

    # ----------------------------------------------------------
    # 3. Backfill existing Collection names.
    # ----------------------------------------------------------

    collections = connection.execute(
        sa.text(
            "SELECT id, name FROM collections"
        )
    ).fetchall()

    for collection in collections:
        connection.execute(
            sa.text(
                """
                UPDATE collections
                SET normalized_name = :normalized_name
                WHERE id = :id
                """
            ),
            {
                "id": collection.id,
                "normalized_name": normalize_text(collection.name)
            }
        )

    # ----------------------------------------------------------
    # 4. Backfill existing Item names.
    # ----------------------------------------------------------

    items = connection.execute(
        sa.text(
            "SELECT id, name FROM items"
        )
    ).fetchall()

    for item in items:
        connection.execute(
            sa.text(
                """
                UPDATE items
                SET normalized_name = :normalized_name
                WHERE id = :id
                """
            ),
            {
                "id": item.id,
                "normalized_name": normalize_text(item.name)
            }
        )

    # ----------------------------------------------------------
    # 5. Make the columns non-nullable.
    # ----------------------------------------------------------

    with op.batch_alter_table(
        "tags",
        schema=None
    ) as batch_op:
        batch_op.alter_column(
            "normalized_name",
            existing_type=sa.String(length=80),
            nullable=False
        )

    with op.batch_alter_table(
        "collections",
        schema=None
    ) as batch_op:
        batch_op.alter_column(
            "normalized_name",
            existing_type=sa.String(length=150),
            nullable=False
        )

    with op.batch_alter_table(
        "items",
        schema=None
    ) as batch_op:
        batch_op.alter_column(
            "normalized_name",
            existing_type=sa.String(length=150),
            nullable=False
        )

    # ----------------------------------------------------------
    # 6. Make normalized Tag names unique.
    # ----------------------------------------------------------

    with op.batch_alter_table(
        "tags",
        schema=None
    ) as batch_op:
        batch_op.create_unique_constraint(
            "uq_tags_normalized_name",
            ["normalized_name"]
        )


def downgrade():
    # Remove the unique constraint first.

    with op.batch_alter_table(
        "tags",
        schema=None
    ) as batch_op:
        batch_op.drop_constraint(
            "uq_tags_normalized_name",
            type_="unique"
        )

        batch_op.drop_column(
            "normalized_name"
        )

    with op.batch_alter_table(
        "items",
        schema=None
    ) as batch_op:
        batch_op.drop_column(
            "normalized_name"
        )

    with op.batch_alter_table(
        "collections",
        schema=None
    ) as batch_op:
        batch_op.drop_column(
            "normalized_name"
        )