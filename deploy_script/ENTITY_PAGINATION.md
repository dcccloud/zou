# Entity sorting and search rollout

The existing `GET /data/entities` endpoint accepts:

- `sort_by`: `name`, `created_at`, or `updated_at`.
- `sort_order`: `asc` or `desc`; defaults to `asc` when sorting is requested.
- `search`: a case-insensitive literal name substring, up to 200 characters. `%` and `_` are literal characters.
- Existing `project_id`, `entity_type_id`, `page`, and `limit` filters still apply.

Filtering and sorting happen before counting and pagination. Name ordering uses the `en` ICU collation with numeric comparison and primary strength, equivalent to `Intl.Collator('en', { numeric: true, sensitivity: 'base' })`. Equal values use ascending entity ID as a tie-breaker. Offset pagination can still shift when entities are edited or removed during browsing.

## Compatibility

Requests without `sort_by`, including an empty or whitespace-only value, retain their previous behavior. `sort_order` is ignored when no sort field is supplied. An empty direction defaults to ascending when a field is supplied. Unsupported nonempty sort fields or invalid directions with an explicit field return 400.

`search` now filters results; older clients that sent this previously ignored parameter will observe this new behavior. Queries with new ordering include `sort_by`, `sort_order`, and normalized `search` in the paginated response, so callers can detect old servers that ignore these parameters.

## Deployment

1. Use a PostgreSQL build with ICU support and the `pg_trgm` extension available. The migration role needs permission to create the collation, extension, and indexes.
2. Run a single migration process using the new Zou code and the target environment's database configuration:

   ```sh
   zou upgrade-db --no-telemetry
   ```

3. Confirm migration `d4e5f6a7b8c9` completed, then enable sorting/search in RavenWeb.

The migration creates a collation and four indexes; it does not change entity columns or business data. Index creation and deletion run concurrently outside a transaction. Existing writers can continue; index builds still consume database resources and can wait for long-running transactions.

Concurrent DDL is not atomic. If the migration fails, rerun the same upgrade command: valid indexes are retained and invalid indexes left by canceled builds are dropped concurrently and rebuilt. Do not run multiple migration processes simultaneously. The shared `pg_trgm` extension is retained on downgrade.

Before the collation is installed, `sort_by=name` returns 503 with a migration instruction. Legacy requests and timestamp sorting do not require that collation. Complete the migration before enabling the new UI.
