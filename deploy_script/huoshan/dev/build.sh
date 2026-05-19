#!/usr/bin/env bash
set -euo pipefail

source ~/.bash_profile

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
PARENT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ -f "$PARENT_DIR/.env" ]; then
    source "$PARENT_DIR/.env"
fi

IMAGE="dcc-cloud2-cn-beijing.cr.volces.com/dcc-cloud/zou-backend:dev"

: "${HUOSHAN_CR_USERNAME:?HUOSHAN_CR_USERNAME is required}"
: "${HUOSHAN_CR_PASSWORD:?HUOSHAN_CR_PASSWORD is required}"
: "${DEV_APIG_GATEWAY_ID:?DEV_APIG_GATEWAY_ID is required}"
: "${DEV_DOMAIN_NAME:?DEV_DOMAIN_NAME is required}"

export DB_HOST="${DEV_DB_HOST:-${DB_HOST:-}}"
export DB_PORT="${DEV_DB_PORT:-${DB_PORT:-5432}}"
export DB_DATABASE="${DEV_DB_DATABASE:-${DB_DATABASE:-}}"
export DB_USERNAME="${DEV_DB_USERNAME:-${DB_USERNAME:-}}"
export DB_PASSWORD="${DEV_DB_PASSWORD:-${DB_PASSWORD:-}}"
export KV_HOST="${DEV_KV_HOST:-${KV_HOST:-}}"
export KV_PORT="${DEV_KV_PORT:-${KV_PORT:-6379}}"
export KV_USERNAME="${DEV_KV_USERNAME:-${KV_USERNAME:-}}"
export KV_PASSWORD="${DEV_KV_PASSWORD:-${KV_PASSWORD:-}}"
export KV_AUTH_TOKEN_BLACKLIST_KV_INDEX="${DEV_KV_AUTH_TOKEN_BLACKLIST_KV_INDEX:-20}"
export KV_MEMOIZE_DB_INDEX="${DEV_KV_MEMOIZE_DB_INDEX:-21}"
export KV_EVENTS_DB_INDEX="${DEV_KV_EVENTS_DB_INDEX:-22}"
export KV_JOB_DB_INDEX="${DEV_KV_JOB_DB_INDEX:-23}"
export KV_CONFIG_DB_INDEX="${DEV_KV_CONFIG_DB_INDEX:-24}"
export SECRET_KEY="${DEV_SECRET_KEY:-${SECRET_KEY:-}}"
export DOMAIN_NAME="$DEV_DOMAIN_NAME"
export DOMAIN_PROTOCOL="${DEV_DOMAIN_PROTOCOL:-https}"
export MAIL_ENABLED="${DEV_MAIL_ENABLED:-False}"
export FS_BACKEND="${DEV_FS_BACKEND:-${FS_BACKEND:-s3}}"
export FS_S3_REGION="${DEV_FS_S3_REGION:-${FS_S3_REGION:-oss-cn-beijing}}"
export FS_S3_ENDPOINT="${DEV_FS_S3_ENDPOINT:-${FS_S3_ENDPOINT:-https://oss-cn-beijing.aliyuncs.com}}"
export FS_S3_ACCESS_KEY="${DEV_FS_S3_ACCESS_KEY:-${FS_S3_ACCESS_KEY:-}}"
export FS_S3_SECRET_KEY="${DEV_FS_S3_SECRET_KEY:-${FS_S3_SECRET_KEY:-}}"
export FS_BUCKET_PREFIX="${DEV_FS_BUCKET_PREFIX:-dcc-kitsu-dev-}"

printf '%s' "$HUOSHAN_CR_PASSWORD" | docker login \
    --username="$HUOSHAN_CR_USERNAME" \
    --password-stdin \
    dcc-cloud2-cn-beijing.cr.volces.com

docker build \
    --platform linux/amd64 \
    -t "$IMAGE" \
    -f "$REPO_ROOT/Dockerfile" \
    "$REPO_ROOT"

docker push "$IMAGE"

cd "$SCRIPT_DIR"
s deploy
