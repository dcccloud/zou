from flask import Blueprint
from flask_jwt_extended import jwt_required

from zou.app.blueprints.capability_jobs.resources import (
    CapabilityJobResource,
    CapabilityJobsResource,
)
from zou.app.utils import permissions
from zou.app.utils.api import configure_api_from_blueprint

routes = [
    ("/data/capability-jobs", CapabilityJobsResource),
    ("/data/capability-jobs/<job_id>", CapabilityJobResource),
]

blueprint = Blueprint("capability_jobs", "capability_jobs")
api = configure_api_from_blueprint(
    blueprint,
    routes,
    decorators=[
        permissions.require_person,
        jwt_required(),
    ],
)
