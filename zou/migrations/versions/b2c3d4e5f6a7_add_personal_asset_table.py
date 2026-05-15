"""add personal_asset table

Revision ID: b2c3d4e5f6a7
Revises: 8d42b9e1f7a3
Create Date: 2026-05-12 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils


# revision identifiers, used by Alembic.
revision = "b2c3d4e5f6a7"
down_revision = "8d42b9e1f7a3"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "personal_asset",
        sa.Column(
            "id",
            sqlalchemy_utils.types.uuid.UUIDType(binary=False),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=250), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("file_name", sa.String(length=250), nullable=True),
        sa.Column("extension", sa.String(length=10), nullable=True),
        sa.Column("file_size", sa.BigInteger(), nullable=True),
        sa.Column("source", sa.String(length=40), nullable=True),
        sa.Column(
            "data", sa.dialects.postgresql.JSONB(), nullable=True
        ),
        sa.Column(
            "person_id",
            sqlalchemy_utils.types.uuid.UUIDType(binary=False),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            sqlalchemy_utils.types.uuid.UUIDType(binary=False),
            nullable=True,
        ),
        sa.Column(
            "entity_id",
            sqlalchemy_utils.types.uuid.UUIDType(binary=False),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["person_id"], ["person.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"]),
        sa.ForeignKeyConstraint(["entity_id"], ["entity.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "name", "person_id", name="personal_asset_uc"
        ),
    )
    with op.batch_alter_table(
        "personal_asset", schema=None
    ) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_personal_asset_person_id"),
            ["person_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_personal_asset_project_id"),
            ["project_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_personal_asset_entity_id"),
            ["entity_id"],
            unique=False,
        )


def downgrade():
    with op.batch_alter_table(
        "personal_asset", schema=None
    ) as batch_op:
        batch_op.drop_index(
            batch_op.f("ix_personal_asset_entity_id")
        )
        batch_op.drop_index(
            batch_op.f("ix_personal_asset_project_id")
        )
        batch_op.drop_index(
            batch_op.f("ix_personal_asset_person_id")
        )
    op.drop_table("personal_asset")
