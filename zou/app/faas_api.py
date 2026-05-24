from zou.app.blueprints.assets import blueprint as assets_blueprint
from zou.app.blueprints.capability_jobs import (
    blueprint as capability_jobs_blueprint,
)
from zou.app.blueprints.comments import blueprint as comments_blueprint
from zou.app.blueprints.crud import blueprint as crud_blueprint
from zou.app.blueprints.departments import blueprint as departments_blueprint
from zou.app.blueprints.entities import blueprint as entities_blueprint
from zou.app.blueprints.personal_assets import (
    blueprint as personal_assets_blueprint,
)
from zou.app.blueprints.persons import blueprint as persons_blueprint
from zou.app.blueprints.playlists.slim import blueprint as playlists_blueprint
from zou.app.blueprints.previews.slim import blueprint as previews_blueprint
from zou.app.blueprints.projects import blueprint as projects_blueprint
from zou.app.blueprints.tasks import blueprint as tasks_blueprint
from zou.app.blueprints.user import blueprint as user_blueprint
from zou.app.blueprints.auth.slim import blueprint as auth_blueprint


def configure(app):
    """
    Configure the reduced HTTP API used by FaaS deployments.

    This profile keeps short request/response CRUD routes for asset and task
    workflows, and intentionally skips plugins, event handlers, Swagger, SAML,
    FIDO, indexer health, import routes, playlist zip routes, preview
    extraction/background routes, and websocket related routes.
    """
    app.url_map.strict_slashes = False
    configure_api_routes(app)
    return app


def configure_api_routes(app):
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(assets_blueprint)
    app.register_blueprint(capability_jobs_blueprint)
    app.register_blueprint(comments_blueprint)
    app.register_blueprint(crud_blueprint)
    app.register_blueprint(departments_blueprint)
    app.register_blueprint(entities_blueprint)
    app.register_blueprint(personal_assets_blueprint)
    app.register_blueprint(persons_blueprint)
    app.register_blueprint(playlists_blueprint)
    app.register_blueprint(previews_blueprint)
    app.register_blueprint(projects_blueprint)
    app.register_blueprint(tasks_blueprint)
    app.register_blueprint(user_blueprint)
    return app
