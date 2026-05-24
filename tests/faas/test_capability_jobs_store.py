import fakeredis

from zou.app.stores import capability_jobs_store


def setup_function():
    capability_jobs_store.capability_jobs_store = (
        fakeredis.FakeStrictRedis(decode_responses=True)
    )


def test_create_and_get_capability_job():
    job = capability_jobs_store.create(
        "indexer",
        "index_asset",
        payload={"asset_id": "asset-1"},
        requested_by="person-1",
        job_id="job-1",
    )

    assert job["id"] == "job-1"
    assert job["capability"] == "indexer"
    assert job["action"] == "index_asset"
    assert job["status"] == capability_jobs_store.STATUS_QUEUED
    assert job["payload"] == {"asset_id": "asset-1"}
    assert job["result"] is None
    assert job["error"] is None
    assert job["requested_by"] == "person-1"

    assert capability_jobs_store.get("job-1") == job


def test_dequeue_marks_job_running():
    capability_jobs_store.create(
        "video-processing",
        "generate_thumbnail",
        payload={"movie_id": "movie-1"},
        job_id="job-1",
    )

    job = capability_jobs_store.dequeue("video-processing")

    assert job["id"] == "job-1"
    assert job["status"] == capability_jobs_store.STATUS_RUNNING
    assert job["started_at"] != ""


def test_mark_succeeded_and_failed_store_structured_payloads():
    capability_jobs_store.create("indexer", "reset_index", job_id="job-1")
    succeeded = capability_jobs_store.mark_succeeded(
        "job-1", result={"reset": True}
    )

    assert succeeded["status"] == capability_jobs_store.STATUS_SUCCEEDED
    assert succeeded["result"] == {"reset": True}
    assert succeeded["finished_at"] != ""

    capability_jobs_store.create("indexer", "reset_index", job_id="job-2")
    failed = capability_jobs_store.mark_failed(
        "job-2", error={"message": "boom"}
    )

    assert failed["status"] == capability_jobs_store.STATUS_FAILED
    assert failed["error"] == {"message": "boom"}
    assert failed["finished_at"] != ""
