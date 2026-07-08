from flask import Blueprint

from zou.app.utils.api import configure_api_from_blueprint

from zou.app.blueprints.raven.resources import (
    EntityPreviewVersionsBundleResource,
    EntityPreviewVersionsBundlesResource,
)

routes = [
    (
        "/data/entities/<entity_id>/preview-versions-bundle",
        EntityPreviewVersionsBundleResource,
    ),
    (
        "/data/raven/preview-versions-bundles",
        EntityPreviewVersionsBundlesResource,
    ),
]

blueprint = Blueprint("raven", "raven")
api = configure_api_from_blueprint(blueprint, routes)
