# FaaS Refactor

This branch introduces a reduced application profile for running short
request/response API workflows on FaaS.

## Goals

- Keep asset, task, project, person, comment, and basic auth APIs available.
- Skip startup work that is not needed for the reduced API profile.
- Keep the full `zou.app:app` behavior unchanged unless
  `ZOU_APP_PROFILE=faas` is set.

## Current FaaS Profile

Set:

```bash
ZOU_APP_PROFILE=faas
```

The FaaS profile skips:

- Swagger/OpenAPI route initialization.
- SAML client initialization.
- FIDO server initialization and FIDO/SAML auth routes.
- Indexer client initialization.
- Plugin loading.
- Event handler registration.
- Import, search, news, export, websocket/event-stream, and index health routes.
- Preview extraction/background routes.
- Playlist zip download/build routes.

It still keeps synchronous CRUD-style API routes for:

- Auth login/logout/authenticated/refresh-token.
- Assets.
- Tasks.
- Projects.
- Persons.
- Departments.
- Entities.
- Comments.
- Personal assets.
- Slim previews for upload/download/thumbnail/annotation workflows.
- Slim playlists for playlist CRUD, add-entity, build job status, and MP4
  build/download workflows.
- Generic `/data` CRUD routes.
- User context/task routes.

In the FaaS profile, movie preview upload stores the source movie in the file
store and enqueues a `video-processing.normalize_movie` capability job. Playlist
MP4 build creates the normal `BuildJob` row and enqueues a
`playlist-build.build_playlist_movie` capability job.

## Next Steps

- Add real workflow smoke coverage for preview upload, playlist MP4 build, and
  index-triggering entity updates.
- Decide whether `/data/capability-jobs` should remain a person-authenticated
  dev endpoint or become internal/admin-only before production.
- Version the shared capability base image if the deployment process needs to
  be fully immutable.
- Add monitoring around queued/running/failed capability jobs.

## Capability FaaS Layout

Each standalone capability lives under `deploy_script/huoshan/capabilities`:

- `indexer`: index updates, removals, and rebuilds.
- `playlist-build`: playlist movie/zip generation.
- `video-processing`: normalization, thumbnail generation, and tile generation.

Each capability folder owns its `s.yaml` and `build.sh`, while shared Docker
build logic lives under `deploy_script/huoshan/capabilities/_common`.

Each capability also owns its own `run.sh`; capability images do not share the
project root `run.sh`. The current Huoshan layout is:

```text
deploy_script/huoshan/capabilities/
  _common/
    Dockerfile.base
    Dockerfile
    build-base.sh
    build-capability.sh
  indexer/
    s.yaml
    build.sh
    run.sh
  playlist-build/
    s.yaml
    build.sh
    run.sh
  video-processing/
    s.yaml
    build.sh
    run.sh
```

`Dockerfile.base` builds the shared Zou runtime image. `_common/Dockerfile`
derives from that base image and copies only the selected capability folder's
`run.sh` into `/opt/application/run.sh`. It also copies the current `zou`
source tree into the final capability image, so capability deploys can pick up
small code changes without rebuilding the shared base image. This keeps the
deployment shape consistent for many FaaS functions while preserving
per-function entrypoints.

The main dev API image defaults to:

```text
dcc-cloud2-cn-beijing.cr.volces.com/dcc-cloud/zou-backend-dev:<utc timestamp>-<git sha>
```

Override it with `DEV_IMAGE_REPOSITORY`, `DEV_IMAGE_TAG`, or `DEV_IMAGE`.

Each capability image similarly defaults to:

```text
dcc-cloud2-cn-beijing.cr.volces.com/dcc-cloud/zou-capability-<name>:<utc timestamp>-<git sha>
```

Override it with `CAPABILITY_IMAGE_REPOSITORY`, `CAPABILITY_IMAGE_TAG`, or
`CAPABILITY_IMAGE`.

## Capability Job Queue

Capability work is represented as Redis-backed jobs. The dev API and capability
functions use `KV_CAPABILITY_JOBS_DB_INDEX`, defaulting to Redis DB `25` for the
Huoshan dev deployment scripts.

The FaaS API exposes:

```text
POST /data/capability-jobs
GET /data/capability-jobs/<job_id>
```

The capability functions expose:

```text
POST /invoke
GET /jobs/<job_id>
POST /dequeue
POST /run-next
POST /run-batch
POST /jobs/<job_id>/succeed
POST /jobs/<job_id>/fail
```

They also expose the same routes under `/capabilities/<capability-name>/...`
so the apps work whether APIG strips the route prefix or forwards it.

`/invoke` and `/data/capability-jobs` both enqueue work and return a `job_id`.
The execution wiring for each capability is intentionally separate from the API
request path so API calls can stay short.
`/run-next` consumes one queued job, while `/run-batch` consumes up to 20 jobs
per invocation. A scheduler can call `/run-batch` to turn the Redis queue into
short FaaS execution bursts.

The Huoshan dev deployment uses async FaaS invocation instead of a separate
scheduler: the main API creates a Redis job, calls the capability
`/run-batch` endpoint, and the platform returns quickly while the capability
continues consuming the batch. Capability mutation and dequeue endpoints require
`X-Capability-Token`. Health routes are intentionally public.

Because Huoshan async invocation accepts the HTTP request before Flask handles
it, an unauthenticated public caller can still receive `202` from APIG. The
Flask token check prevents queue mutation/consumption inside the function, but
production should also protect capability routes at the APIG layer, call only
private/inner URLs from the main API, or avoid exposing capability routes
publicly.

The `indexer` capability wires `/run-next` to the existing index service for
`index_asset`, `index_person`, `index_shot`, removals, and `reset_index`.
When `ZOU_APP_PROFILE=faas`, calls through `index_service` enqueue indexer jobs
instead of touching Meilisearch directly.

The `video-processing` capability wires `/run-next` to movie normalization,
thumbnail generation, and tile generation. Payloads pass file-store references
instead of file contents.

The `playlist-build` capability wires `/run-next` to playlist movie and zip
generation. Movie output is written to the existing movie store under
`playlists/<build_job_id>`. Zip output is written to the file store under
`playlist-zips/<capability_job_id>` by default.
