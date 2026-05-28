from flask import Blueprint
from flask_jwt_extended import jwt_required

from zou.app.utils.api import configure_api_from_blueprint
from zou.app.utils import permissions

from zou.app.blueprints.personal_assets.resources import (
    PersonalAssetsResource,
    PersonalAssetResource,
    PromotePersonalAssetResource,
)

routes = [
    ("/data/user/personal-assets", PersonalAssetsResource),
    (
        "/data/user/personal-assets/<personal_asset_id>",
        PersonalAssetResource,
    ),
    (
        "/data/user/personal-assets/<personal_asset_id>/promote",
        PromotePersonalAssetResource,
    ),
]

blueprint = Blueprint("personal_assets", "personal_assets")
api = configure_api_from_blueprint(
    blueprint,
    routes,
    decorators=[
        permissions.require_person,
        jwt_required(),
    ],
)
