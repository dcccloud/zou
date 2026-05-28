import datetime
import json
import sys
import uuid

import redis

from zou.app import config

JOB_KEY_PREFIX = "capability-job"
QUEUE_KEY_PREFIX = "capability-queue"

STATUS_QUEUED = "queued"
STATUS_RUNNING = "running"
STATUS_SUCCEEDED = "succeeded"
STATUS_FAILED = "failed"


try:
    capability_jobs_store = redis.StrictRedis(
        host=config.KEY_VALUE_STORE["host"],
        port=config.KEY_VALUE_STORE["port"],
        db=config.KV_CAPABILITY_JOBS_DB_INDEX,
        username=config.KEY_VALUE_STORE.get("username"),
        password=config.KEY_VALUE_STORE["password"],
        decode_responses=True,
    )
    capability_jobs_store.ping()
except redis.ConnectionError:
    capability_jobs_store = None
    if "pytest" not in sys.modules:
        print("Cannot access to the required Redis instance")


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _job_key(job_id):
    return f"{JOB_KEY_PREFIX}:{job_id}"


def _queue_key(capability):
    return f"{QUEUE_KEY_PREFIX}:{capability}"


def _serialize(value):
    return json.dumps(value or {})


def _deserialize(value):
    if not value:
        return None
    return json.loads(value)


def _require_store():
    if capability_jobs_store is None:
        raise RuntimeError("Capability jobs store is not available")


def create(capability, action, payload=None, requested_by=None, job_id=None):
    _require_store()
    job_id = job_id or str(uuid.uuid4())
    now = _now()
    job = {
        "id": job_id,
        "capability": capability,
        "action": action,
        "status": STATUS_QUEUED,
        "payload": _serialize(payload),
        "result": "",
        "error": "",
        "requested_by": requested_by or "",
        "created_at": now,
        "updated_at": now,
        "started_at": "",
        "finished_at": "",
    }
    capability_jobs_store.hset(_job_key(job_id), mapping=job)
    capability_jobs_store.rpush(_queue_key(capability), job_id)
    return get(job_id)


def get(job_id):
    _require_store()
    data = capability_jobs_store.hgetall(_job_key(job_id))
    if not data:
        return None
    data["payload"] = _deserialize(data.get("payload")) or {}
    data["result"] = _deserialize(data.get("result"))
    data["error"] = _deserialize(data.get("error"))
    return data


def list_jobs(capability=None, action=None, status=None, limit=50):
    _require_store()
    limit = max(1, min(int(limit or 50), 200))
    jobs = []
    for key in capability_jobs_store.scan_iter(f"{JOB_KEY_PREFIX}:*"):
        job_id = key.split(":", 1)[1]
        job = get(job_id)
        if job is None:
            continue
        if capability and job.get("capability") != capability:
            continue
        if action and job.get("action") != action:
            continue
        if status and job.get("status") != status:
            continue
        jobs.append(job)

    jobs.sort(key=lambda item: item.get("created_at") or "", reverse=True)
    return jobs[:limit]


def dequeue(capability):
    _require_store()
    job_id = capability_jobs_store.lpop(_queue_key(capability))
    if job_id is None:
        return None
    return mark_started(job_id)


def mark_started(job_id):
    _require_store()
    now = _now()
    capability_jobs_store.hset(
        _job_key(job_id),
        mapping={
            "status": STATUS_RUNNING,
            "started_at": now,
            "updated_at": now,
        },
    )
    return get(job_id)


def mark_succeeded(job_id, result=None):
    _require_store()
    now = _now()
    capability_jobs_store.hset(
        _job_key(job_id),
        mapping={
            "status": STATUS_SUCCEEDED,
            "result": _serialize(result),
            "updated_at": now,
            "finished_at": now,
        },
    )
    return get(job_id)


def mark_failed(job_id, error=None):
    _require_store()
    now = _now()
    capability_jobs_store.hset(
        _job_key(job_id),
        mapping={
            "status": STATUS_FAILED,
            "error": _serialize(error),
            "updated_at": now,
            "finished_at": now,
        },
    )
    return get(job_id)
