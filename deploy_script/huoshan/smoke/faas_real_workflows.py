#!/usr/bin/env python3
import argparse
import json
import mimetypes
import os
import sys
import time
from pathlib import Path
from urllib import error, parse, request


DEFAULT_API_URL = "https://sd86fns4l0ar2klup4mrg.apigateway-cn-beijing.volceapi.com"
TRANSIENT_STATUS_CODES = {408, 409, 425, 429, 500, 502, 503, 504}
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MOVIE_FIXTURE = REPO_ROOT / "tests/fixtures/videos/test_preview_tiles.mp4"


def env(name, default=None):
    value = os.getenv(name)
    return value if value not in (None, "") else default


def join_url(base, path):
    return f"{base.rstrip('/')}/{path.lstrip('/')}"


def encode_multipart(fields, files):
    boundary = f"----zou-faas-smoke-{int(time.time() * 1000)}"
    chunks = []
    for name, value in fields.items():
        chunks.extend(
            [
                f"--{boundary}\r\n".encode(),
                (
                    f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
                ).encode(),
                str(value).encode(),
                b"\r\n",
            ]
        )
    for name, file_path in files.items():
        path = Path(file_path)
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        chunks.extend(
            [
                f"--{boundary}\r\n".encode(),
                (
                    f'Content-Disposition: form-data; name="{name}"; '
                    f'filename="{path.name}"\r\n'
                ).encode(),
                f"Content-Type: {mime}\r\n\r\n".encode(),
                path.read_bytes(),
                b"\r\n",
            ]
        )
    chunks.append(f"--{boundary}--\r\n".encode())
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def request_once(method, api_url, path, payload=None, token=None, files=None):
    data = None
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if files:
        data, content_type = encode_multipart(payload or {}, files)
        headers["Content-Type"] = content_type
    elif payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = request.Request(
        join_url(api_url, path),
        data=data,
        headers=headers,
        method=method,
    )
    try:
        with request.urlopen(req, timeout=120) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body) if body else None
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        try:
            parsed = json.loads(body) if body else None
        except json.JSONDecodeError:
            parsed = body
        return exc.code, parsed
    except error.URLError as exc:
        return 0, {"error": True, "message": str(exc)}


def request_api(
    method,
    api_url,
    path,
    payload=None,
    token=None,
    files=None,
    expected=None,
    retries=3,
):
    last_status = None
    last_body = None
    for attempt in range(retries + 1):
        status, body = request_once(
            method, api_url, path, payload=payload, token=token, files=files
        )
        last_status = status
        last_body = body
        if status not in TRANSIENT_STATUS_CODES and status != 0:
            break
        if attempt < retries:
            print(
                f"retrying {method} {path}: HTTP {status} "
                f"(attempt {attempt + 1}/{retries})"
            )
            time.sleep(3)
    if expected is not None and last_status != expected:
        print(json.dumps(last_body, indent=2, ensure_ascii=False))
        raise SystemExit(
            f"{method} {path} expected HTTP {expected}, got {last_status}"
        )
    return last_status, last_body


def get_token(api_url):
    token = env("ZOU_ACCESS_TOKEN")
    if token:
        return token

    email = env("ZOU_EMAIL")
    password = env("ZOU_PASSWORD")
    if not email or not password:
        raise SystemExit("Set ZOU_ACCESS_TOKEN or ZOU_EMAIL/ZOU_PASSWORD.")

    _status, body = request_api(
        "POST",
        api_url,
        "/auth/login",
        payload={"email": email, "password": password},
        expected=200,
    )
    return body["access_token"]


def rows_from(body):
    if isinstance(body, dict) and "data" in body:
        return body["data"]
    return body if isinstance(body, list) else []


def first_row(api_url, token, path, label, predicate=None):
    _status, body = request_api("GET", api_url, path, token=token, expected=200)
    rows = rows_from(body)
    for row in rows:
        if predicate is None or predicate(row):
            return row
    raise SystemExit(f"No usable {label} found via {path}.")


def get_job(api_url, token, job_id):
    _status, body = request_api(
        "GET",
        api_url,
        f"/data/capability-jobs/{job_id}",
        token=token,
        expected=200,
    )
    return body


def poll_job(api_url, token, job_id, timeout_seconds=180):
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        job = get_job(api_url, token, job_id)
        status = job.get("status")
        print(f"capability job {job_id}: {job.get('capability')}.{job.get('action')} {status}")
        if status in {"succeeded", "failed"}:
            return job
        time.sleep(5)
    raise SystemExit(f"Timed out waiting for capability job {job_id}.")


def smoke_preview_upload(api_url, token, task, movie_path, poll):
    task_id = task["id"]
    status_id = task["task_status_id"]
    _status, comment = request_api(
        "POST",
        api_url,
        f"/actions/tasks/{task_id}/comment",
        payload={
            "task_status_id": status_id,
            "comment": f"FaaS real smoke preview {int(time.time())}",
        },
        token=token,
        expected=201,
    )
    _status, preview = request_api(
        "POST",
        api_url,
        f"/actions/tasks/{task_id}/comments/{comment['id']}/add-preview",
        payload={"revision": 0},
        token=token,
        expected=201,
    )
    _status, uploaded = request_api(
        "POST",
        api_url,
        f"/movies/originals/preview-files/{preview['id']}.mp4",
        token=token,
        files={"file": movie_path},
        expected=201,
    )
    job_id = ((uploaded or {}).get("data") or {}).get("video_processing_job_id")
    if not job_id:
        raise SystemExit("Preview upload did not return video_processing_job_id.")
    print(f"preview upload queued video-processing job: {job_id}")
    if poll:
        return poll_job(api_url, token, job_id)
    return get_job(api_url, token, job_id)


def smoke_playlist_build(api_url, token, project_id, poll):
    name = f"faas-smoke-{int(time.time())}"
    _status, playlist = request_api(
        "POST",
        api_url,
        "/data/playlists",
        payload={"name": name, "project_id": project_id, "shots": []},
        token=token,
        expected=201,
    )
    _status, build_job = request_api(
        "GET",
        api_url,
        f"/data/playlists/{playlist['id']}/build/mp4",
        token=token,
        expected=200,
    )
    capability_job_id = build_job.get("capability_job_id")
    if not capability_job_id:
        raise SystemExit("Playlist build did not return capability_job_id.")
    print(
        f"playlist build created BuildJob {build_job['id']} "
        f"and capability job {capability_job_id}"
    )
    if poll:
        return poll_job(api_url, token, capability_job_id)
    return get_job(api_url, token, capability_job_id)


def smoke_indexer(api_url, token, entity, poll):
    marker = f"faas-smoke-{int(time.time())}"
    data = entity.get("data") or {}
    data["faas_smoke_marker"] = marker
    _status, updated = request_api(
        "PUT",
        api_url,
        f"/data/entities/{entity['id']}",
        payload={"data": data},
        token=token,
        expected=200,
    )

    query = parse.urlencode({"capability": "indexer", "limit": 30})
    _status, body = request_api(
        "GET",
        api_url,
        f"/data/capability-jobs?{query}",
        token=token,
        expected=200,
    )
    entity_id = updated["id"]
    jobs = [
        job for job in body.get("jobs", [])
        if entity_id in json.dumps(job.get("payload") or {})
    ]
    if not jobs:
        raise SystemExit(f"No recent indexer job found for entity {entity_id}.")
    job_id = jobs[0]["id"]
    print(f"entity update queued indexer job: {job_id}")
    if poll:
        return poll_job(api_url, token, job_id)
    return get_job(api_url, token, job_id)


def main():
    parser = argparse.ArgumentParser(
        description="Real workflow smoke tests for the Zou FaaS deployment."
    )
    parser.add_argument("--api-url", default=env("ZOU_API_URL", DEFAULT_API_URL))
    parser.add_argument(
        "--movie",
        default=str(DEFAULT_MOVIE_FIXTURE),
        help="Small MP4 fixture used for preview upload.",
    )
    parser.add_argument("--poll", action="store_true")
    args = parser.parse_args()

    movie_path = Path(args.movie)
    if not movie_path.exists():
        raise SystemExit(f"Movie fixture does not exist: {movie_path}")

    token = get_token(args.api_url)
    task = first_row(args.api_url, token, "/data/tasks?limit=20", "task")
    entity = first_row(
        args.api_url,
        token,
        "/data/entities?limit=100",
        "asset or shot entity",
        lambda row: row.get("type") in {"Asset", "Shot"},
    )

    results = {
        "preview": smoke_preview_upload(
            args.api_url, token, task, str(movie_path), args.poll
        ),
        "playlist": smoke_playlist_build(
            args.api_url, token, task["project_id"], args.poll
        ),
        "indexer": smoke_indexer(args.api_url, token, entity, args.poll),
    }
    print("real workflow smoke summary:")
    for name, job in results.items():
        print(
            f"- {name}: {job.get('capability')}.{job.get('action')} "
            f"{job.get('status')}"
        )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
