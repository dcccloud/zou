from tests.base import ApiDBTestCase
from zou.app.models.personal_asset import PersonalAsset
from zou.app.utils import fields


class PersonalAssetTestCase(ApiDBTestCase):
    def setUp(self):
        super(PersonalAssetTestCase, self).setUp()
        self.generate_data(PersonalAsset, 3, person_id=self.user["id"])

    def test_get_personal_assets(self):
        personal_assets = self.get("data/personal-assets")
        self.assertEqual(len(personal_assets), 3)

    def test_get_personal_asset(self):
        personal_asset = self.get_first("data/personal-assets")
        personal_asset_again = self.get(
            "data/personal-assets/%s" % personal_asset["id"]
        )
        self.assertEqual(personal_asset["id"], personal_asset_again["id"])
        self.get_404("data/personal-assets/%s" % fields.gen_uuid())

    def test_create_personal_asset(self):
        data = {
            "name": "Test Asset",
            "person_id": self.user["id"],
            "source": "chat",
        }
        self.post("data/personal-assets", data)
        personal_assets = self.get("data/personal-assets")
        self.assertEqual(len(personal_assets), 4)

    def test_update_personal_asset(self):
        personal_asset = self.get_first("data/personal-assets")
        data = {"description": "Updated description"}
        self.put("data/personal-assets/%s" % personal_asset["id"], data)
        personal_asset_again = self.get(
            "data/personal-assets/%s" % personal_asset["id"]
        )
        self.assertEqual(
            personal_asset_again["description"],
            data["description"],
        )

    def test_delete_personal_asset(self):
        personal_assets = self.get("data/personal-assets")
        self.assertEqual(len(personal_assets), 3)
        self.delete("data/personal-assets/%s" % personal_assets[0]["id"])
        personal_assets = self.get("data/personal-assets")
        self.assertEqual(len(personal_assets), 2)
