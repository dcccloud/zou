from tests.base import ApiDBTestCase


class PersonalAssetRoutesTestCase(ApiDBTestCase):
    def setUp(self):
        super(PersonalAssetRoutesTestCase, self).setUp()
        self.generate_fixture_project_status()
        self.generate_fixture_project()
        self.generate_fixture_asset_type()

    def test_list_personal_assets(self):
        self.post("data/user/personal-assets", {"name": "Asset 1"})
        self.post("data/user/personal-assets", {"name": "Asset 2"})
        assets = self.get("data/user/personal-assets")
        self.assertEqual(len(assets), 2)

    def test_create_personal_asset(self):
        data = {
            "name": "Chat Image",
            "source": "chat",
            "extension": "png",
            "file_size": 1024,
        }
        result = self.post("data/user/personal-assets", data)
        self.assertEqual(result["name"], "Chat Image")
        self.assertEqual(result["source"], "chat")
        self.assertEqual(result["person_id"], self.user["id"])

    def test_get_personal_asset(self):
        created = self.post("data/user/personal-assets", {"name": "My Asset"})
        fetched = self.get("data/user/personal-assets/%s" % created["id"])
        self.assertEqual(fetched["id"], created["id"])

    def test_update_personal_asset(self):
        created = self.post("data/user/personal-assets", {"name": "My Asset"})
        updated = self.put(
            "data/user/personal-assets/%s" % created["id"],
            {"description": "Updated"},
        )
        self.assertEqual(updated["description"], "Updated")

    def test_delete_personal_asset(self):
        created = self.post("data/user/personal-assets", {"name": "My Asset"})
        self.delete("data/user/personal-assets/%s" % created["id"])
        self.get("data/user/personal-assets/%s" % created["id"], 404)

    def test_promote_to_entity(self):
        created = self.post(
            "data/user/personal-assets",
            {"name": "Promotable Asset"},
        )
        data = {
            "project_id": str(self.project.id),
            "asset_type_id": str(self.asset_type.id),
        }
        result = self.post(
            "data/user/personal-assets/%s/promote" % created["id"],
            data,
        )
        self.assertIsNotNone(result["entity_id"])
        self.assertEqual(result["project_id"], str(self.project.id))

    def test_non_owner_cannot_access(self):
        created = self.post("data/user/personal-assets", {"name": "Private"})
        self.generate_fixture_user_cg_artist()
        self.log_in_cg_artist()
        self.get("data/user/personal-assets/%s" % created["id"], 403)

    def test_admin_can_access_any(self):
        self.generate_fixture_user_cg_artist()
        self.log_in_cg_artist()
        created = self.post(
            "data/user/personal-assets",
            {"name": "Artist Asset"},
        )
        self.log_in_admin()
        fetched = self.get("data/user/personal-assets/%s" % created["id"])
        self.assertEqual(fetched["id"], created["id"])
