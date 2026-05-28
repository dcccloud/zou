#!/usr/bin/env bash
set -euo pipefail

source ~/.bash_profile

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [ -f "$SCRIPT_DIR/.env" ]; then
    source "$SCRIPT_DIR/.env"
fi

IMAGE="dcc-cloud2-cn-beijing.cr.volces.com/dcc-cloud/zou-backend:0.0.4"
: "${HUOSHAN_CR_USERNAME:?HUOSHAN_CR_USERNAME is required}"
: "${HUOSHAN_CR_PASSWORD:?HUOSHAN_CR_PASSWORD is required}"

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
