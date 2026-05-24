#!/usr/bin/env bash
set -euo pipefail

source ~/.bash_profile

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

IMAGE="registry.cn-hangzhou.aliyuncs.com/dcc-cloud/zou-backend:0.0.1"

docker login \
    --username=kevinsun@1461585705826999 \
    --password=dcc2024cloud \
    registry.cn-hangzhou.aliyuncs.com

docker build \
    --platform linux/amd64 \
    -t "$IMAGE" \
    -f "$REPO_ROOT/Dockerfile" \
    "$REPO_ROOT"

docker push "$IMAGE"

cd "$SCRIPT_DIR"
s deploy
