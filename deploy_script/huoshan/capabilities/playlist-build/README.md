# Playlist Build Capability

Standalone FaaS boundary for playlist movie/zip generation.

Endpoint contract:

- `GET /healthz`
- `POST /invoke`
- `GET /jobs/<job_id>`
- `POST /dequeue`
- `POST /run-next`
- `POST /run-batch`
- `POST /jobs/<job_id>/succeed`
- `POST /jobs/<job_id>/fail`

Supported actions:

- `build_playlist_movie`
- `build_playlist_zip`

The same endpoints are also available below the gateway prefix, for example
`POST /capabilities/playlist-build/invoke`.

Example movie payload:

```json
{
  "action": "build_playlist_movie",
  "payload": {
    "playlist_id": "00000000-0000-0000-0000-000000000000",
    "full": false
  }
}
```

The movie output is stored in the existing Zou movie store under
`playlists/<build_job_id>`.

Example zip payload:

```json
{
  "action": "build_playlist_zip",
  "payload": {
    "playlist_id": "00000000-0000-0000-0000-000000000000"
  }
}
```

The zip output is stored in the file store under
`playlist-zips/<capability_job_id>` unless `output_prefix` or `output_id` is
provided in the payload.

Run up to 10 queued jobs:

```bash
curl -X POST "$PLAYLIST_BUILD_URL/run-batch" \
  -H "X-Capability-Token: $FAAS_CAPABILITY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"limit": 10}'
```

Deploy:

```bash
PLAYLIST_BUILD_APIG_GATEWAY_ID=... ./build.sh
```
