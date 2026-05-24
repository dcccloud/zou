# Indexer Capability

Standalone FaaS boundary for index updates and index rebuild work.

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
`POST /capabilities/indexer/run-batch`.

Supported actions:

- `index_asset`
- `index_person`
- `index_shot`
- `remove_asset`
- `remove_person`
- `remove_shot`
- `reset_index`

Payload fields:

- `index_asset`: `{"asset_id": "..."}`
- `index_person`: `{"person_id": "..."}`
- `index_shot`: `{"shot_id": "..."}`
- `remove_asset`: `{"asset_id": "..."}`
- `remove_person`: `{"person_id": "..."}`
- `remove_shot`: `{"shot_id": "..."}`
- `reset_index`: `{}`

Run one queued job:

```bash
curl -X POST "$INDEXER_URL/run-next" \
  -H "X-Capability-Token: $FAAS_CAPABILITY_TOKEN"
```

Run up to 10 queued jobs:

```bash
curl -X POST "$INDEXER_URL/run-batch" \
  -H "X-Capability-Token: $FAAS_CAPABILITY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"limit": 10}'
```

Deploy:

```bash
INDEXER_APIG_GATEWAY_ID=... ./build.sh
```
