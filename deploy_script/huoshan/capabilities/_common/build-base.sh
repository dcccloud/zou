#!/usr/bin/env bash
set -euo pipefail

source ~/.bash_profile

COMMON_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$COMMON_DIR/../../../.." && pwd)"
HUOSHAN_DIR="$(cd "$COMMON_DIR/../.." && pwd)"

if [ -f "$HUOSHAN_DIR/.env" ]; then
    source "$HUOSHAN_DIR/.env"
fi

: "${HUOSHAN_CR_USERNAME:?HUOSHAN_CR_USERNAME is required}"
: "${HUOSHAN_CR_PASSWORD:?HUOSHAN_CR_PASSWORD is required}"

CAPABILITY_BASE_IMAGE="${CAPABILITY_BASE_IMAGE:-dcc-cloud2-cn-beijing.cr.volces.com/dcc-cloud/zou-capability-base:dev}"

printf '%s' "$HUOSHAN_CR_PASSWORD" | docker login \
    --username="$HUOSHAN_CR_USERNAME" \
    --password-stdin \
    dcc-cloud2-cn-beijing.cr.volces.com

docker build \
    --platform linux/amd64 \
    -t "$CAPABILITY_BASE_IMAGE" \
    -f "$COMMON_DIR/Dockerfile.base" \
    "$REPO_ROOT"

docker push "$CAPABILITY_BASE_IMAGE"
