#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [ -f "$REPO_ROOT/.env" ]; then
    set -a
    # shellcheck source=/dev/null
    source "$REPO_ROOT/.env"
    set +a
fi

if [ -f "$SCRIPT_DIR/.env" ]; then
    set -a
    # shellcheck source=/dev/null
    source "$SCRIPT_DIR/.env"
    set +a
fi

export FS_S3_ACCESS_KEY="${FS_S3_ACCESS_KEY:-${EXTERNAL_S3_ACCESS_KEY:-}}"
export FS_S3_SECRET_KEY="${FS_S3_SECRET_KEY:-${EXTERNAL_S3_SECRET_KEY:-}}"
export FS_S3_REGION="${FS_S3_REGION:-${EXTERNAL_S3_REGION:-}}"
export FS_S3_ENDPOINT="${FS_S3_ENDPOINT:-${EXTERNAL_S3_ENDPOINT:-}}"

: "${DB_PASSWORD:?DB_PASSWORD is required for deploy}"
: "${KV_PASSWORD:?KV_PASSWORD is required for deploy}"
: "${SECRET_KEY:?SECRET_KEY is required for deploy}"
: "${FS_S3_ACCESS_KEY:?FS_S3_ACCESS_KEY or EXTERNAL_S3_ACCESS_KEY is required}"
: "${FS_S3_SECRET_KEY:?FS_S3_SECRET_KEY or EXTERNAL_S3_SECRET_KEY is required}"

cd "$SCRIPT_DIR"
s deploy
