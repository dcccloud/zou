import importlib
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from tests.base import ApiTestCase
from zou.app import db


class EntityIndexMigrationTestCase(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.engine = db.engine
        self.migration = importlib.import_module(
            "zou.migrations.versions.d4e5f6a7b8c9_add_entity_natural_sort"
        )

    def run_migration(self, direction):
        with self.engine.connect() as connection:
            context = MigrationContext.configure(connection)
            with patch.object(self.migration, "op", Operations(context)):
                with context.begin_transaction():
                    getattr(self.migration, direction)()

    def test_upgrade_allows_writes_and_can_resume_failed_concurrent_indexes(
        self,
    ):
        self.run_migration("upgrade")
        with self.engine.connect().execution_options(
            isolation_level="AUTOCOMMIT"
        ) as connection:
            connection.execute(
                text("DROP INDEX CONCURRENTLY ix_entity_project_type_created")
            )

        with self.engine.connect() as writer, ThreadPoolExecutor(
            max_workers=1
        ) as executor:
            writer.execute(text("LOCK TABLE entity IN ROW EXCLUSIVE MODE"))
            pending = executor.submit(self.run_migration, "upgrade")
            try:
                with self.engine.connect().execution_options(
                    isolation_level="AUTOCOMMIT"
                ) as observer:
                    deadline = time.monotonic() + 10
                    progress = None
                    while time.monotonic() < deadline:
                        progress = observer.execute(
                            text(
                                "SELECT pid, command FROM pg_stat_progress_create_index "
                                "WHERE relid = 'entity'::regclass AND phase = 'waiting for writers before build'"
                            )
                        ).first()
                        if progress:
                            break
                        if pending.done():
                            pending.result()
                            self.fail(
                                "Index build completed without waiting for the open writer"
                            )
                        time.sleep(0.01)
                    self.assertIsNotNone(progress)
                    self.assertEqual(
                        progress.command, "CREATE INDEX CONCURRENTLY"
                    )
                    observer.execute(text("SET lock_timeout = '1s'"))
                    observer.execute(
                        text("UPDATE entity SET name = name WHERE false")
                    )
                    observer.execute(
                        text("SELECT pg_cancel_backend(:pid)"),
                        {"pid": progress.pid},
                    )
                    with self.assertRaises(OperationalError) as canceled:
                        pending.result(timeout=5)
                    self.assertEqual(canceled.exception.orig.sqlstate, "57014")
            finally:
                writer.rollback()
                if not pending.done():
                    pending.result(timeout=5)

        with self.engine.connect() as connection:
            self.assertFalse(
                connection.execute(
                    text(
                        "SELECT indisvalid FROM pg_index WHERE indexrelid = 'ix_entity_project_type_created'::regclass"
                    )
                ).scalar()
            )
        self.run_migration("upgrade")
        self.run_migration("upgrade")
        with self.engine.connect() as connection:
            for name, _definition in self.migration.INDEXES:
                self.assertTrue(
                    connection.execute(
                        text(
                            "SELECT indisvalid FROM pg_index WHERE indexrelid = to_regclass(:name)"
                        ),
                        {"name": name},
                    ).scalar()
                )
        self.run_migration("downgrade")
        with self.engine.connect() as connection:
            for name, _definition in self.migration.INDEXES:
                self.assertIsNone(
                    connection.execute(
                        text("SELECT to_regclass(:name)"), {"name": name}
                    ).scalar()
                )
        self.run_migration("upgrade")
