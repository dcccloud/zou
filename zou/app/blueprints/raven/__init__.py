from flask import Blueprint

from zou.app.utils.api import configure_api_from_blueprint

from zou.app.blueprints.raven.resources import (
    EntityPreviewVersionsBundleResource,
)

routes = [
    (
        "/data/entities/<entity_id>/preview-versions-bundle",
        EntityPreviewVersionsBundleResource,
    ),
]

blueprint = Blueprint("raven", "raven")
api = configure_api_from_blueprint(blueprint, routes)
