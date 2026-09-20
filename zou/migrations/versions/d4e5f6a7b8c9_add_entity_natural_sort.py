from alembic import op
from sqlalchemy import text

revision = "d4e5f6a7b8c9"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None

INDEXES = (
    (
        "ix_entity_project_type_natural_name",
        "ON entity (project_id, entity_type_id, name COLLATE raven_natural_name, id)",
    ),
    (
        "ix_entity_project_type_created",
        "ON entity (project_id, entity_type_id, created_at, id)",
    ),
    (
        "ix_entity_project_type_updated",
        "ON entity (project_id, entity_type_id, updated_at, id)",
    ),
    ("ix_entity_name_search", "ON entity USING gin (name gin_trgm_ops)"),
)


def upgrade():
    op.execute(
        "CREATE COLLATION IF NOT EXISTS raven_natural_name "
        "(provider = icu, locale = 'en-u-kn-true-ks-level1', deterministic = false)"
    )
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    with op.get_context().autocommit_block():
        for name, definition in INDEXES:
            valid = (
                op.get_bind()
                .execute(
                    text(
                        "SELECT indisvalid FROM pg_index WHERE indexrelid = to_regclass(:name)"
                    ),
                    {"name": name},
                )
                .scalar()
            )
            if valid is False:
                op.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {name}")
            op.execute(
                f"CREATE INDEX CONCURRENTLY IF NOT EXISTS {name} {definition}"
            )


def downgrade():
    with op.get_context().autocommit_block():
        for name, _definition in reversed(INDEXES):
            op.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {name}")
    op.execute("DROP COLLATION IF EXISTS raven_natural_name")
