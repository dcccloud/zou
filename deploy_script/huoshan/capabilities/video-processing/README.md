# Video Processing Capability

Standalone FaaS boundary for preview video processing.

Endpoint contract:

- `GET /healthz`
- `POST /invoke`
- `GET /jobs/<job_id>`
- `POST /dequeue`
- `POST /run-next`
- `POST /run-batch`
- `POST /jobs/<job_id>/succeed`
- `POST /jobs/<job_id>/fail`

The same endpoints are also available below the gateway prefix, for example
`POST /capabilities/video-processing/run-batch`.

Supported actions:

- `normalize_movie`
- `generate_thumbnail`
- `generate_tile`

Payload fields:

- `normalize_movie`:
  `{"preview_file_id": "...", "movie_id": "...", "prefix": "source", "extension": ".mov"}`
- `generate_thumbnail`:
  `{"movie_id": "...", "prefix": "previews", "extension": ".mp4", "picture_id": "..."}`
- `generate_tile`:
  `{"movie_id": "...", "prefix": "previews", "extension": ".mp4", "tile_id": "..."}`

`movie_id` refers to an existing movie object in the configured file store.
The action downloads it to `/tmp`, processes it, and writes results back to the
configured file store when an output id is supplied.

Run one queued job:

```bash
curl -X POST "$VIDEO_PROCESSING_URL/run-next" \
  -H "X-Capability-Token: $FAAS_CAPABILITY_TOKEN"
```

Run up to 10 queued jobs:

```bash
curl -X POST "$VIDEO_PROCESSING_URL/run-batch" \
  -H "X-Capability-Token: $FAAS_CAPABILITY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"limit": 10}'
```

Deploy:

```bash
VIDEO_PROCESSING_APIG_GATEWAY_ID=... ./build.sh
```
