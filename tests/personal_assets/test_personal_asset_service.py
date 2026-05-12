from tests.base import ApiDBTestCase
from zou.app.services import personal_assets_service
from zou.app.services.exception import (
    PersonalAssetNotFoundException,
)
from zou.app.utils import fields


class PersonalAssetServiceTestCase(ApiDBTestCase):
    def setUp(self):
        super(PersonalAssetServiceTestCase, self).setUp()
        self.generate_fixture_project_status()
        self.generate_fixture_project()
        self.generate_fixture_asset_type()

    def test_create_personal_asset(self):
        result = personal_assets_service.create_personal_asset(
            person_id=self.user["id"],
            name="Test Asset",
            source="chat",
        )
        self.assertIsNotNone(result["id"])
        self.assertEqual(result["name"], "Test Asset")

    def test_get_personal_asset(self):
        created = personal_assets_service.create_personal_asset(
            person_id=self.user["id"],
            name="Test",
        )
        fetched = personal_assets_service.get_personal_asset(created["id"])
        self.assertEqual(fetched["id"], created["id"])

    def test_get_personal_asset_not_found(self):
        self.assertRaises(
            PersonalAssetNotFoundException,
            personal_assets_service.get_personal_asset,
            fields.gen_uuid(),
        )

    def test_get_personal_assets_for_person(self):
        personal_assets_service.create_personal_asset(
            person_id=self.user["id"], name="A1"
        )
        personal_assets_service.create_personal_asset(
            person_id=self.user["id"], name="A2"
        )
        results = personal_assets_service.get_personal_assets_for_person(
            self.user["id"]
        )
        self.assertEqual(len(results), 2)

    def test_update_personal_asset(self):
        created = personal_assets_service.create_personal_asset(
            person_id=self.user["id"], name="Test"
        )
        updated = personal_assets_service.update_personal_asset(
            created["id"], {"description": "New desc"}
        )
        self.assertEqual(updated["description"], "New desc")

    def test_delete_personal_asset(self):
        created = personal_assets_service.create_personal_asset(
            person_id=self.user["id"], name="Test"
        )
        personal_assets_service.delete_personal_asset(created["id"])
        self.assertRaises(
            PersonalAssetNotFoundException,
            personal_assets_service.get_personal_asset,
            created["id"],
        )

    def test_promote_to_entity(self):
        created = personal_assets_service.create_personal_asset(
            person_id=self.user["id"], name="Promotable"
        )
        result = personal_assets_service.promote_to_entity(
            created["id"],
            project_id=str(self.project.id),
            asset_type_id=str(self.asset_type.id),
        )
        self.assertIsNotNone(result["entity_id"])
        self.assertEqual(result["project_id"], str(self.project.id))
