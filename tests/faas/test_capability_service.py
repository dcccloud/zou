import fakeredis

from zou.app.services import capability_service
from zou.app.stores import capability_jobs_store
from zou.faas_capabilities.common import app, require_capability_token


def setup_function():
    capability_jobs_store.capability_jobs_store = (
        fakeredis.FakeStrictRedis(decode_responses=True)
    )


def test_get_run_batch_url_appends_capability_route(monkeypatch):
    monkeypatch.setattr(
        capability_service.config,
        "FAAS_CAPABILITY_INDEXER_URL",
        "https://indexer.example.com",
    )

    assert (
        capability_service.get_run_batch_url("indexer")
        == "https://indexer.example.com/capabilities/indexer/run-batch"
    )


def test_get_run_batch_url_accepts_route_root(monkeypatch):
    monkeypatch.setattr(
        capability_service.config,
        "FAAS_CAPABILITY_PLAYLIST_BUILD_URL",
        "https://playlist.example.com/capabilities/playlist-build",
    )

    assert (
        capability_service.get_run_batch_url("playlist-build")
        == "https://playlist.example.com/capabilities/playlist-build/run-batch"
    )


def test_create_job_triggers_capability(monkeypatch):
    calls = []

    class Response:
        status_code = 202

        def raise_for_status(self):
            return None

    def post(url, json=None, headers=None, timeout=None):
        calls.append(
            {
                "url": url,
                "json": json,
                "headers": headers,
                "timeout": timeout,
            }
        )
        return Response()

    monkeypatch.setattr(
        capability_service.config,
        "FAAS_CAPABILITY_VIDEO_PROCESSING_URL",
        "https://video.example.com",
    )
    monkeypatch.setattr(
        capability_service.config,
        "FAAS_CAPABILITY_TOKEN",
        "token-1",
    )
    monkeypatch.setattr(
        capability_service.config,
        "FAAS_CAPABILITY_TRIGGER_BATCH_SIZE",
        12,
    )
    monkeypatch.setattr(
        capability_service.config,
        "FAAS_CAPABILITY_TRIGGER_TIMEOUT",
        1.5,
    )
    monkeypatch.setattr(capability_service.requests, "post", post)

    job, trigger = capability_service.create_job(
        "video-processing",
        "normalize_movie",
        payload={"preview_file_id": "preview-1"},
        job_id="job-1",
    )

    assert job["id"] == "job-1"
    assert trigger["triggered"] is True
    assert calls == [
        {
            "url": (
                "https://video.example.com"
                "/capabilities/video-processing/run-batch"
            ),
            "json": {"limit": 12},
            "headers": {"X-Capability-Token": "token-1"},
            "timeout": 1.5,
        }
    ]


def test_capability_token_uses_config_default(monkeypatch):
    monkeypatch.setattr(
        capability_service.config,
        "FAAS_CAPABILITY_TOKEN",
        "expected-token",
    )

    @require_capability_token
    def protected():
        return {"ok": True}

    with app.test_request_context(headers={}):
        response, status = protected()

    assert status == 403
    assert response.get_json() == {"error": True, "message": "Forbidden"}

    with app.test_request_context(
        headers={"X-Capability-Token": "expected-token"}
    ):
        assert protected() == {"ok": True}
