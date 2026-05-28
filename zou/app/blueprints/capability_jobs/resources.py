from flask_restful import Resource

from zou.app.mixin import ArgsMixin
from zou.app.services import capability_service
from zou.app.stores import capability_jobs_store
from zou.faas_capabilities.actions import CAPABILITY_ACTIONS


class CapabilityJobsResource(Resource, ArgsMixin):
    def get(self):
        options = self.get_args(
            [
                ("capability", None, False),
                ("action", None, False),
                ("status", None, False),
                ("limit", 50, False, int),
            ],
            location=["args"],
        )
        return {
            "jobs": capability_jobs_store.list_jobs(
                capability=options["capability"],
                action=options["action"],
                status=options["status"],
                limit=options["limit"],
            )
        }

    def post(self):
        body = self.get_args(
            [
                ("capability", None, True),
                ("action", None, True),
                ("payload", {}, False, dict),
                ("requested_by", None, False),
                ("job_id", None, False),
            ]
        )

        capability = body["capability"]
        action = body["action"]
        supported_actions = CAPABILITY_ACTIONS.get(capability)
        if supported_actions is None:
            return (
                {
                    "error": True,
                    "message": "Unsupported capability.",
                    "supported_capabilities": list(CAPABILITY_ACTIONS.keys()),
                },
                400,
            )
        if action not in supported_actions:
            return (
                {
                    "error": True,
                    "message": "Unsupported action.",
                    "supported_actions": supported_actions,
                },
                400,
            )

        job, trigger = capability_service.create_job(
            capability,
            action,
            payload=body["payload"],
            requested_by=body["requested_by"],
            job_id=body["job_id"],
        )
        return {
            "accepted": True,
            "job_id": job["id"],
            "job": job,
            "trigger": trigger,
        }, 202


class CapabilityJobResource(Resource):
    def get(self, job_id):
        job = capability_jobs_store.get(job_id)
        if job is None:
            return {"error": True, "message": "Job not found."}, 404
        return job
