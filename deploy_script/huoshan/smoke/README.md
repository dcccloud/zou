# Zou FaaS Smoke Tests

## 1. Health-only smoke

This does not create jobs:

```bash
python deploy_script/huoshan/smoke/faas_smoke.py
```

Expected:

- main API `/` returns `404`
- main API `/auth/authenticated` returns `401`
- each async capability health route returns `202`

## 2. Manual capability enqueue smoke

This creates three synthetic jobs through the main API and triggers the async
capabilities:

```bash
export ZOU_ACCESS_TOKEN="<jwt access token>"
python deploy_script/huoshan/smoke/faas_smoke.py --enqueue --poll
```

Alternatively:

```bash
export ZOU_EMAIL="<login email>"
export ZOU_PASSWORD="<login password>"
python deploy_script/huoshan/smoke/faas_smoke.py --enqueue --poll
```

The synthetic payloads use fake IDs. The jobs may finish as `failed`; for this
smoke, that is acceptable because the goal is to verify that the main API
creates jobs, triggers async FaaS, and records a final job state.

The script retries transient `403`, `429`, and `5xx` responses because a fresh
FaaS deploy can briefly mix old and new instances while APIG and image sync
settle. It does not print access tokens.

Capability execution endpoints require `X-Capability-Token` inside the Flask
app. On Huoshan async functions, APIG can still return `202` before the app
handles the request, so route-level token checks should be paired with APIG or
private-network protection before production exposure.

Expected synthetic outcomes:

- `indexer.remove_asset` can succeed because removing a missing ID is harmless.
- `playlist-build.build_playlist_movie` usually fails with fake playlist/build
  UUIDs.
- `video-processing.generate_thumbnail` usually fails with a fake movie UUID.

## 3. Real workflow smoke

After the synthetic smoke passes, run the real user workflows:

1. Upload a movie preview and check the returned preview data contains a
   `video_processing_job_id`.
2. Build a playlist MP4 and check a `BuildJob` row is created and later updated.
3. Create or update an asset/shot/person and confirm an `indexer` job is queued
   and consumed.
