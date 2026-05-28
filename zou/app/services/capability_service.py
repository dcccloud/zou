import os

import requests

from zou.app import app, config
from zou.app.stores import capability_jobs_store


CAPABILITY_URLS = {
    "indexer": "FAAS_CAPABILITY_INDEXER_URL",
    "playlist-build": "FAAS_CAPABILITY_PLAYLIST_BUILD_URL",
    "video-processing": "FAAS_CAPABILITY_VIDEO_PROCESSING_URL",
}


def is_faas_profile():
    return os.getenv("ZOU_APP_PROFILE") == "faas"


def create_job(capability, action, payload=None, requested_by=None, job_id=None):
    job = capability_jobs_store.create(
        capability,
        action,
        payload=payload or {},
        requested_by=requested_by,
        job_id=job_id,
    )
    trigger = trigger_capability(capability)
    return job, trigger


def get_capability_url(capability):
    env_name = CAPABILITY_URLS.get(capability)
    if env_name is None:
        return None
    return getattr(config, env_name, None)


def get_run_batch_url(capability):
    base_url = get_capability_url(capability)
    if not base_url:
        return None

    base_url = base_url.rstrip("/")
    route_prefix = f"/capabilities/{capability}"
    if base_url.endswith("/run-batch"):
        return base_url
    if base_url.endswith(route_prefix):
        return f"{base_url}/run-batch"
    return f"{base_url}{route_prefix}/run-batch"


def trigger_capability(capability, limit=None):
    url = get_run_batch_url(capability)
    if not url:
        app.logger.warning(
            "Capability %s was queued but no trigger URL is configured.",
            capability,
        )
        return {"triggered": False, "reason": "missing_url"}

    headers = {}
    if config.FAAS_CAPABILITY_TOKEN:
        headers["X-Capability-Token"] = config.FAAS_CAPABILITY_TOKEN

    payload = {"limit": limit or config.FAAS_CAPABILITY_TRIGGER_BATCH_SIZE}
    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=config.FAAS_CAPABILITY_TRIGGER_TIMEOUT,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        app.logger.error(
            "Failed to trigger capability %s at %s",
            capability,
            url,
            exc_info=1,
        )
        return {
            "triggered": False,
            "reason": "request_failed",
            "error": str(exc),
        }

    return {
        "triggered": True,
        "status_code": response.status_code,
        "url": url,
    }
