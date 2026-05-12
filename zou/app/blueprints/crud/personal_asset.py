from flask_jwt_extended import jwt_required

from zou.app.models.personal_asset import PersonalAsset
from zou.app.blueprints.crud.base import BaseModelResource, BaseModelsResource
from zou.app.services import personal_assets_service
from zou.app.utils import permissions


class PersonalAssetsResource(BaseModelsResource):
    def __init__(self):
        BaseModelsResource.__init__(self, PersonalAsset)

    def check_read_permissions(self, options=None):
        return permissions.check_admin_permissions()

    def check_create_permissions(self, data):
        return permissions.check_admin_permissions()

    @jwt_required()
    def get(self):
        return super().get()

    @jwt_required()
    def post(self):
        return super().post()


class PersonalAssetResource(BaseModelResource):
    def __init__(self):
        BaseModelResource.__init__(self, PersonalAsset)

    def check_read_permissions(self, instance_dict):
        personal_assets_service.check_personal_asset_access(instance_dict)
        return True

    def check_update_permissions(self, instance_dict, data):
        personal_assets_service.check_personal_asset_access(instance_dict)
        return True

    def check_delete_permissions(self, instance_dict):
        personal_assets_service.check_personal_asset_access(instance_dict)
        return True

    @jwt_required()
    def get(self, instance_id):
        return super().get(instance_id)

    @jwt_required()
    def put(self, instance_id):
        return super().put(instance_id)

    @jwt_required()
    def delete(self, instance_id):
        return super().delete(instance_id)
