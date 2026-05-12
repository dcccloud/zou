from flask_restful import Resource

from zou.app.mixin import ArgsMixin
from zou.app.services import personal_assets_service, persons_service
from zou.app.utils import validation
from zou.app.blueprints.personal_assets.schemas import (
    CreatePersonalAssetSchema,
    UpdatePersonalAssetSchema,
    PromotePersonalAssetSchema,
)


class PersonalAssetsResource(Resource, ArgsMixin):
    def get(self):
        current_user = persons_service.get_current_user()
        return personal_assets_service.get_personal_assets_for_person(
            current_user["id"]
        )

    def post(self):
        body = validation.validate_request_body(CreatePersonalAssetSchema)
        current_user = persons_service.get_current_user()
        return (
            personal_assets_service.create_personal_asset(
                person_id=current_user["id"],
                name=body.name,
                description=body.description,
                file_name=body.file_name,
                extension=body.extension,
                file_size=body.file_size,
                source=body.source,
                data=body.data,
                project_id=(str(body.project_id) if body.project_id else None),
            ),
            201,
        )


class PersonalAssetResource(Resource, ArgsMixin):
    def get(self, personal_asset_id):
        personal_asset = personal_assets_service.get_personal_asset(
            personal_asset_id
        )
        personal_assets_service.check_personal_asset_access(personal_asset)
        return personal_asset

    def put(self, personal_asset_id):
        personal_asset = personal_assets_service.get_personal_asset(
            personal_asset_id
        )
        personal_assets_service.check_personal_asset_access(personal_asset)
        body = validation.validate_request_body(UpdatePersonalAssetSchema)
        data = body.model_dump(exclude_none=True)
        if "project_id" in data:
            data["project_id"] = str(data["project_id"])
        return personal_assets_service.update_personal_asset(
            personal_asset_id, data
        )

    def delete(self, personal_asset_id):
        personal_asset = personal_assets_service.get_personal_asset(
            personal_asset_id
        )
        personal_assets_service.check_personal_asset_access(personal_asset)
        personal_assets_service.delete_personal_asset(personal_asset_id)
        return "", 204


class PromotePersonalAssetResource(Resource, ArgsMixin):
    def post(self, personal_asset_id):
        personal_asset = personal_assets_service.get_personal_asset(
            personal_asset_id
        )
        personal_assets_service.check_personal_asset_access(personal_asset)
        body = validation.validate_request_body(PromotePersonalAssetSchema)
        return (
            personal_assets_service.promote_to_entity(
                personal_asset_id,
                project_id=str(body.project_id),
                asset_type_id=str(body.asset_type_id),
            ),
            201,
        )
