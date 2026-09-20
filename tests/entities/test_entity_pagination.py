import importlib
from datetime import datetime, timedelta
from unittest.mock import patch
from urllib.parse import urlencode

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import text

from tests.base import ApiDBTestCase
from zou.app import app, db
from zou.app.models.entity import Entity


class EntityPaginationTestCase(ApiDBTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        migration = importlib.import_module(
            "zou.migrations.versions.d4e5f6a7b8c9_add_entity_natural_sort"
        )
        with app.app_context(), db.engine.connect() as connection:
            context = MigrationContext.configure(connection)
            with patch.object(migration, "op", Operations(context)):
                with context.begin_transaction():
                    migration.upgrade()
                with context.begin_transaction():
                    migration.upgrade()

    def setUp(self):
        super().setUp()
        self.generate_fixture_project_status()
        self.generate_fixture_project()
        self.generate_fixture_sequence()
        self.shots = [
            self.generate_fixture_shot(name=name)
            for name in (
                "分镜10",
                "分镜2",
                "分镜1",
                "SHOT10",
                "shot2",
                "SHOT02",
                "50%_完成",
                "50XY完成",
            )
        ]
        for index, shot in enumerate(self.shots):
            Entity.query.filter_by(id=shot.id).update(
                {
                    "created_at": datetime(2026, 1, 1) + timedelta(days=index),
                    "updated_at": datetime(2026, 2, 1) - timedelta(days=index),
                }
            )
        db.session.commit()

    def query_page(self, **options):
        params = {
            "project_id": str(self.project.id),
            "entity_type_id": str(self.shot_type.id),
            "page": 1,
            "limit": 2,
        }
        params.update(options)
        return self.get("/data/entities?" + urlencode(params))

    def test_natural_name_order_and_search_across_pages(self):
        first = self.query_page(sort_by="name", search="分镜")
        second = self.query_page(sort_by="name", search="分镜", page=2)
        self.assertEqual(
            [row["name"] for row in first["data"]], ["分镜1", "分镜2"]
        )
        self.assertEqual([row["name"] for row in second["data"]], ["分镜10"])
        self.assertEqual(first["total"], 3)
        self.assertEqual(first["nb_pages"], 2)
        self.assertEqual(first["sort_by"], "name")
        self.assertEqual(first["search"], "分镜")
        descending = self.query_page(
            sort_by="name", sort_order="desc", search="分镜"
        )
        self.assertEqual(
            [row["name"] for row in descending["data"]], ["分镜10", "分镜2"]
        )

    def test_case_insensitive_natural_ties_use_id(self):
        result = self.query_page(sort_by="name", search="shot", limit=10)
        expected = sorted(self.shots[4:6], key=lambda shot: str(shot.id)) + [
            self.shots[3]
        ]
        self.assertEqual(
            [row["id"] for row in result["data"]],
            [str(shot.id) for shot in expected],
        )

    def test_all_time_directions_apply_before_limit(self):
        for field, direction, indexes in (
            ("created_at", "asc", [0, 1]),
            ("created_at", "desc", [7, 6]),
            ("updated_at", "asc", [7, 6]),
            ("updated_at", "desc", [0, 1]),
        ):
            with self.subTest(field=field, direction=direction):
                result = self.query_page(sort_by=field, sort_order=direction)
                self.assertEqual(
                    [row["id"] for row in result["data"]],
                    [str(self.shots[index].id) for index in indexes],
                )

    def test_literal_search_and_empty_results(self):
        self.assertEqual(
            self.query_page(sort_by="name", search="%_")["total"], 1
        )
        self.assertEqual(
            self.query_page(sort_by="name", search="  SHOT  ")["total"], 3
        )
        result = self.query_page(sort_by="name", search="missing")
        self.assertEqual(result["total"], 0)
        self.assertEqual(result["data"], [])

    def test_project_and_permission_filters_still_apply(self):
        self.generate_fixture_project_standard()
        Entity.create(
            name="分镜0",
            project_id=self.project_standard.id,
            entity_type_id=self.shot_type.id,
        )
        self.assertEqual(
            self.query_page(sort_by="name", search="分镜")["total"], 3
        )
        self.generate_fixture_user_cg_artist()
        self.log_in_cg_artist()
        self.assertEqual(
            self.query_page(sort_by="name", search="分镜")["total"], 0
        )

    def test_invalid_sort_and_oversized_search_are_rejected(self):
        for options in (
            {"sort_by": "id; DROP TABLE entity"},
            {"sort_by": "name", "sort_order": "invalid"},
            {"search": "x" * 201},
        ):
            with self.subTest(options=options):
                self.get(
                    "/data/entities?" + urlencode({"page": 1, **options}), 400
                )

    def test_existing_default_order_is_unchanged(self):
        result = self.query_page()
        self.assertEqual(
            [row["id"] for row in result["data"]],
            [str(shot.id) for shot in self.shots[:2]],
        )
        self.assertNotIn("sort_by", result)

    def test_empty_sort_parameters_keep_legacy_order(self):
        expected = self.query_page()
        for options in (
            {"sort_by": ""},
            {"sort_by": " ", "sort_order": "invalid"},
            {"sort_order": "invalid"},
        ):
            with self.subTest(options=options):
                result = self.query_page(**options)
                self.assertEqual(result, expected)
        self.assertEqual(
            self.query_page(sort_by="name", sort_order="", search="分镜")[
                "data"
            ][0]["name"],
            "分镜1",
        )

    def test_missing_migration_only_blocks_natural_name_sorting(self):
        db.session.execute(
            text("DROP INDEX ix_entity_project_type_natural_name")
        )
        db.session.execute(text("DROP COLLATION raven_natural_name"))
        self.assertEqual(self.query_page()["total"], len(self.shots))
        self.assertEqual(
            self.query_page(sort_by="created_at")["total"], len(self.shots)
        )
        result = self.get("/data/entities?page=1&sort_by=name", 503)
        self.assertIn("zou upgrade-db", result["message"])
