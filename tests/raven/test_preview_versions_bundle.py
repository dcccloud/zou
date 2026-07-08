from tests.base import ApiDBTestCase


class RavenPreviewVersionsBundleTestCase(ApiDBTestCase):
    def setUp(self):
        super(RavenPreviewVersionsBundleTestCase, self).setUp()
        self.generate_fixture_project_status()
        self.generate_fixture_project()
        self.generate_fixture_asset_type()
        self.generate_fixture_asset()
        self.generate_fixture_department()
        self.generate_fixture_task_type()
        self.generate_fixture_task_status()
        self.generate_fixture_task_status_wip()
        self.generate_fixture_person()
        self.generate_fixture_assigner()
        self.generate_fixture_task()

        self.task_id = str(self.task.id)
        self.entity_id = str(self.asset.id)
        self.wip_status_id = str(self.task_status_wip.id)

    def create_comment_with_preview(self, text, revision=None):
        comment = self.post(
            f"/actions/tasks/{self.task_id}/comment/",
            {"task_status_id": self.wip_status_id, "comment": text},
        )
        preview = self.post(
            f"/actions/tasks/{self.task_id}/comments/{comment['id']}/add-preview",
            {"revision": revision} if revision else {},
        )
        return comment, preview

    def test_bundle_returns_joined_versions(self):
        comment1, preview1 = self.create_comment_with_preview(
            "first", revision=1
        )
        comment2, preview2 = self.create_comment_with_preview(
            "second", revision=2
        )

        bundle = self.get(
            "data/entities/%s/preview-versions-bundle" % self.entity_id
        )

        self.assertEqual(bundle["entity_id"], self.entity_id)
        versions = bundle["versions"]
        self.assertEqual(len(versions), 2)

        self.assertEqual(versions[0]["preview_file"]["id"], preview1["id"])
        self.assertEqual(versions[0]["preview_file"]["revision"], 1)
        self.assertEqual(versions[0]["comment_id"], comment1["id"])
        self.assertEqual(versions[0]["comment_text"], "first")
        self.assertEqual(versions[0]["task_id"], self.task_id)
        self.assertEqual(
            versions[0]["task_type_id"], str(self.task_type.id)
        )
        self.assertEqual(
            versions[0]["task_type_name"], self.task_type.name
        )

        self.assertEqual(versions[1]["preview_file"]["id"], preview2["id"])
        self.assertEqual(versions[1]["preview_file"]["revision"], 2)
        self.assertEqual(versions[1]["comment_text"], "second")

    def test_bundle_empty_for_entity_without_previews(self):
        bundle = self.get(
            "data/entities/%s/preview-versions-bundle" % self.entity_id
        )
        self.assertEqual(bundle["entity_id"], self.entity_id)
        self.assertEqual(bundle["versions"], [])

    def test_bundle_missing_entity_returns_404(self):
        self.get(
            "data/entities/00000000-0000-0000-0000-000000000000/"
            "preview-versions-bundle",
            404,
        )

    def test_batch_bundles(self):
        comment1, preview1 = self.create_comment_with_preview(
            "first", revision=1
        )
        missing_id = "00000000-0000-0000-0000-000000000000"

        result = self.get(
            "data/raven/preview-versions-bundles?entity_ids=%s,%s"
            % (self.entity_id, missing_id)
        )

        bundles = result["bundles"]
        self.assertEqual(len(bundles), 2)
        self.assertEqual(bundles[0]["entity_id"], self.entity_id)
        self.assertEqual(len(bundles[0]["versions"]), 1)
        self.assertEqual(
            bundles[0]["versions"][0]["preview_file"]["id"], preview1["id"]
        )
        self.assertEqual(bundles[1]["entity_id"], missing_id)
        self.assertEqual(bundles[1]["versions"], [])

    def test_batch_bundles_rejects_invalid_ids(self):
        self.get(
            "data/raven/preview-versions-bundles?entity_ids=not-a-uuid", 400
        )

    def test_batch_bundles_empty_input(self):
        result = self.get("data/raven/preview-versions-bundles?entity_ids=")
        self.assertEqual(result["bundles"], [])
