import os
import uuid
from functools import wraps

from flask import jsonify, request

os.environ.setdefault("ZOU_APP_PROFILE", "capability")

from zou.app import app, config  # noqa: E402
from zou.app.stores import capability_jobs_store  # noqa: E402


def require_capability_token(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        expected_token = config.FAAS_CAPABILITY_TOKEN
        if expected_token:
            actual_token = request.headers.get("X-Capability-Token")
            if actual_token != expected_token:
                return jsonify({"error": True, "message": "Forbidden"}), 403
        return function(*args, **kwargs)

    return wrapper


def register_capability_routes(
    capability_name, supported_actions, execute_job=None
):
    route_prefix = f"/capabilities/{capability_name}"

    def _execute_and_mark(job):
        try:
            result = execute_job(job)
            job = capability_jobs_store.mark_succeeded(
                job["id"], result=result or {}
            )
            return job, None
        except Exception as exc:
            app.logger.error(
                "Capability job %s failed", job["id"], exc_info=1
            )
            job = capability_jobs_store.mark_failed(
                job["id"],
                error={
                    "type": exc.__class__.__name__,
                    "message": str(exc),
                },
            )
            return job, exc

    @app.get("/")
    @app.get(route_prefix)
    @app.get("/healthz")
    @app.get(f"{route_prefix}/healthz")
    def healthz():
        return {
            "ok": True,
            "capability": capability_name,
            "supported_actions": supported_actions,
        }

    @app.post("/invoke")
    @app.post(f"{route_prefix}/invoke")
    @require_capability_token
    def invoke():
        payload = request.get_json(silent=True) or {}
        action = payload.get("action")
        if action not in supported_actions:
            return (
                jsonify(
                    {
                        "error": True,
                        "message": "Unsupported action.",
                        "supported_actions": supported_actions,
                    }
                ),
                400,
            )

        job = capability_jobs_store.create(
            capability_name,
            action,
            payload=payload.get("payload") or {},
            requested_by=payload.get("requested_by"),
            job_id=payload.get("job_id") or str(uuid.uuid4()),
        )
        app.logger.info(
            "Queued %s capability action %s for job %s",
            capability_name,
            action,
            job["id"],
        )
        return (
            jsonify(
                {
                    "accepted": True,
                    "capability": capability_name,
                    "action": action,
                    "job_id": job["id"],
                    "job": job,
                }
            ),
            202,
        )

    @app.get("/jobs/<job_id>")
    @app.get(f"{route_prefix}/jobs/<job_id>")
    @require_capability_token
    def get_job(job_id):
        job = capability_jobs_store.get(job_id)
        if job is None:
            return jsonify({"error": True, "message": "Job not found"}), 404
        return job

    @app.post("/dequeue")
    @app.post(f"{route_prefix}/dequeue")
    @require_capability_token
    def dequeue():
        job = capability_jobs_store.dequeue(capability_name)
        if job is None:
            return jsonify({"empty": True})
        return job

    @app.post("/run-next")
    @app.post(f"{route_prefix}/run-next")
    @require_capability_token
    def run_next():
        if execute_job is None:
            return (
                jsonify(
                    {
                        "error": True,
                        "message": "Capability execution is not wired yet.",
                    }
                ),
                501,
            )

        job = capability_jobs_store.dequeue(capability_name)
        if job is None:
            return jsonify({"empty": True})

        job, error = _execute_and_mark(job)
        if error is None:
            return {"executed": True, "job": job}
        return {"executed": False, "job": job}, 500

    @app.post("/run-batch")
    @app.post(f"{route_prefix}/run-batch")
    @require_capability_token
    def run_batch():
        if execute_job is None:
            return (
                jsonify(
                    {
                        "error": True,
                        "message": "Capability execution is not wired yet.",
                    }
                ),
                501,
            )

        payload = request.get_json(silent=True) or {}
        try:
            limit = int(payload.get("limit") or request.args.get("limit") or 1)
        except (TypeError, ValueError):
            return (
                jsonify(
                    {
                        "error": True,
                        "message": "limit must be an integer.",
                    }
                ),
                400,
            )
        limit = max(1, min(limit, 20))
        results = []
        failed = 0

        for _ in range(limit):
            job = capability_jobs_store.dequeue(capability_name)
            if job is None:
                break
            job, error = _execute_and_mark(job)
            if error is not None:
                failed += 1
            results.append({"executed": error is None, "job": job})

        return {
            "empty": len(results) == 0,
            "count": len(results),
            "failed": failed,
            "results": results,
        }

    @app.post("/jobs/<job_id>/succeed")
    @app.post(f"{route_prefix}/jobs/<job_id>/succeed")
    @require_capability_token
    def mark_succeeded(job_id):
        payload = request.get_json(silent=True) or {}
        job = capability_jobs_store.mark_succeeded(
            job_id, result=payload.get("result") or {}
        )
        return job

    @app.post("/jobs/<job_id>/fail")
    @app.post(f"{route_prefix}/jobs/<job_id>/fail")
    @require_capability_token
    def mark_failed(job_id):
        payload = request.get_json(silent=True) or {}
        job = capability_jobs_store.mark_failed(
            job_id, error=payload.get("error") or {}
        )
        return job

    return app
