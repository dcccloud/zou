#!/usr/bin/env python3
import argparse
import json
import os
import sys
import time
from urllib import error, request


DEFAULT_API_URL = "https://sd86fns4l0ar2klup4mrg.apigateway-cn-beijing.volceapi.com"
DEFAULT_CAPABILITIES = {
    "indexer": "https://sd86mim923h0slf5sfavg.apigateway-cn-beijing.volceapi.com",
    "playlist-build": "https://sd86ml0sl0ar2klupd21g.apigateway-cn-beijing.volceapi.com",
    "video-processing": "https://sd86mmkcl0ar2klupd4t0.apigateway-cn-beijing.volceapi.com",
}
TRANSIENT_STATUS_CODES = {403, 408, 409, 425, 429, 500, 502, 503, 504}
EXPECTED_SYNTHETIC_FAILURES = {
    ("playlist-build", "build_playlist_movie"):
        "expected with the synthetic fake playlist/build UUIDs",
    ("video-processing", "generate_thumbnail"):
        "expected with the synthetic fake movie UUID",
}


def env(name, default=None):
    value = os.getenv(name)
    return value if value not in (None, "") else default


def join_url(base, path):
    return f"{base.rstrip('/')}/{path.lstrip('/')}"


def request_json_once(method, url, payload=None, headers=None, timeout=30):
    data = None
    request_headers = headers.copy() if headers else {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        request_headers["Content-Type"] = "application/json"

    req = request.Request(
        url,
        data=data,
        headers=request_headers,
        method=method,
    )
    try:
        with request.urlopen(req, timeout=timeout) as response:
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


def request_json(
    method,
    url,
    payload=None,
    headers=None,
    timeout=30,
    retries=3,
    retry_delay=3,
):
    last_status = None
    last_body = None
    for attempt in range(retries + 1):
        status, body = request_json_once(
            method,
            url,
            payload=payload,
            headers=headers,
            timeout=timeout,
        )
        last_status = status
        last_body = body
        if status not in TRANSIENT_STATUS_CODES and status != 0:
            return status, body
        if attempt < retries:
            print(
                f"retrying {method} {url}: HTTP {status} "
                f"(attempt {attempt + 1}/{retries})"
            )
            time.sleep(retry_delay)
    return last_status, last_body


def expect_status(
    label,
    method,
    url,
    expected,
    payload=None,
    headers=None,
    retries=3,
    retry_delay=3,
):
    status, body = request_json(
        method,
        url,
        payload=payload,
        headers=headers,
        retries=retries,
        retry_delay=retry_delay,
    )
    print(f"{label}: HTTP {status}")
    if status != expected:
        print(json.dumps(body, indent=2, ensure_ascii=False))
        raise SystemExit(f"{label} expected HTTP {expected}, got {status}")
    return body


def get_access_token(api_url):
    token = env("ZOU_ACCESS_TOKEN")
    if token:
        return token

    email = env("ZOU_EMAIL")
    password = env("ZOU_PASSWORD")
    if not email or not password:
        return None

    status, body = request_json(
        "POST",
        join_url(api_url, "/auth/login"),
        payload={"email": email, "password": password},
    )
    if status != 200 or not body or not body.get("access_token"):
        raise SystemExit(
            "Login failed. Set ZOU_ACCESS_TOKEN directly or check "
            "ZOU_EMAIL/ZOU_PASSWORD."
        )
    return body["access_token"]


def capability_url(name):
    env_name = "FAAS_CAPABILITY_" + name.upper().replace("-", "_") + "_URL"
    return env(env_name, DEFAULT_CAPABILITIES[name])


def health_checks(api_url):
    expect_status("main /", "GET", join_url(api_url, "/"), 404)
    expect_status(
        "main /auth/authenticated",
        "GET",
        join_url(api_url, "/auth/authenticated"),
        401,
    )
    for name in DEFAULT_CAPABILITIES:
        url = join_url(capability_url(name), f"/capabilities/{name}/healthz")
        expect_status(f"{name} healthz async trigger", "GET", url, 202)


def enqueue_job(api_url, token, capability, action, payload):
    headers = {"Authorization": f"Bearer {token}"}
    status, body = request_json(
        "POST",
        join_url(api_url, "/data/capability-jobs"),
        payload={
            "capability": capability,
            "action": action,
            "payload": payload,
            "requested_by": "faas-smoke",
        },
        headers=headers,
    )
    print(f"enqueue {capability}.{action}: HTTP {status}")
    if status != 202:
        print(json.dumps(body, indent=2, ensure_ascii=False))
        raise SystemExit(f"Failed to enqueue {capability}.{action}")
    return body["job_id"], body


def get_job(api_url, token, job_id):
    headers = {"Authorization": f"Bearer {token}"}
    status, body = request_json(
        "GET",
        join_url(api_url, f"/data/capability-jobs/{job_id}"),
        headers=headers,
    )
    if status != 200:
        print(f"get job {job_id}: HTTP {status}")
        print(json.dumps(body, indent=2, ensure_ascii=False))
        raise SystemExit(f"Failed to read job {job_id}")
    return body


def describe_job(job):
    capability = job.get("capability")
    action = job.get("action")
    status = job.get("status")
    label = f"{capability}.{action}"
    expected_note = EXPECTED_SYNTHETIC_FAILURES.get((capability, action))
    if status == "succeeded":
        return f"{label}: succeeded"
    if status == "failed" and expected_note:
        error_body = job.get("error") or {}
        error_type = error_body.get("type") or "error"
        return f"{label}: failed ({expected_note}; {error_type})"
    return f"{label}: {status}"


def poll_jobs(api_url, token, job_ids, timeout_seconds=90):
    deadline = time.time() + timeout_seconds
    pending = set(job_ids)
    final = {}

    while pending and time.time() < deadline:
        for job_id in list(pending):
            job = get_job(api_url, token, job_id)
            status = job.get("status")
            print(f"job {job_id}: {status}")
            if status in {"succeeded", "failed"}:
                final[job_id] = job
                pending.remove(job_id)
        if pending:
            time.sleep(5)

    if pending:
        raise SystemExit(f"Timed out waiting for jobs: {sorted(pending)}")
    return final


def enqueue_smoke_jobs(api_url, poll):
    token = get_access_token(api_url)
    if not token:
        raise SystemExit(
            "Set ZOU_ACCESS_TOKEN, or set ZOU_EMAIL and ZOU_PASSWORD, "
            "before running --enqueue."
        )

    fake_id = "00000000-0000-4000-8000-000000000001"
    jobs = []
    jobs.append(
        enqueue_job(
            api_url,
            token,
            "indexer",
            "remove_asset",
            {"asset_id": fake_id},
        )[0]
    )
    jobs.append(
        enqueue_job(
            api_url,
            token,
            "playlist-build",
            "build_playlist_movie",
            {
                "playlist_id": fake_id,
                "build_job_id": fake_id,
                "full": False,
                "width": 1280,
                "height": 720,
                "fps": 24,
            },
        )[0]
    )
    jobs.append(
        enqueue_job(
            api_url,
            token,
            "video-processing",
            "generate_thumbnail",
            {"movie_id": fake_id},
        )[0]
    )

    if poll:
        final = poll_jobs(api_url, token, jobs)
        for job_id, job in final.items():
            print(f"{job_id}: {describe_job(job)}")
    else:
        print("queued job ids:", ", ".join(jobs))


def main():
    parser = argparse.ArgumentParser(
        description="Smoke tests for the Zou FaaS deployment."
    )
    parser.add_argument(
        "--api-url",
        default=env("ZOU_API_URL", DEFAULT_API_URL),
        help="Main Zou API URL.",
    )
    parser.add_argument(
        "--enqueue",
        action="store_true",
        help="Create three smoke capability jobs through the main API.",
    )
    parser.add_argument(
        "--poll",
        action="store_true",
        help="Poll enqueued smoke jobs until succeeded or failed.",
    )
    args = parser.parse_args()

    health_checks(args.api_url)
    if args.enqueue:
        enqueue_smoke_jobs(args.api_url, args.poll)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
