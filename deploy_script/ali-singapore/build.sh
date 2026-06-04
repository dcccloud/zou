#!/usr/bin/env bash
set -euo pipefail

if [ -f ~/.bash_profile ]; then
    source ~/.bash_profile
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

usage() {
    echo "Usage: $0 [--login-only]"
}

LOGIN_ONLY=false
if [ "${1:-}" = "--login-only" ]; then
    LOGIN_ONLY=true
    shift
fi

if [ "$#" -ne 0 ]; then
    usage
    exit 2
fi

if [ -f "$REPO_ROOT/.env" ]; then
    set -a
    source "$REPO_ROOT/.env"
    set +a
fi

if [ -f "$SCRIPT_DIR/.env" ]; then
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
fi

REGISTRY="${ALI_SINGAPORE_REGISTRY_PUBLIC:-${ALI_MALAYSIA_REGISTRY_PUBLIC:-raven-sg-registry.ap-southeast-1.cr.aliyuncs.com}}"
REGISTRY_USERNAME="${ALI_SINGAPORE_REGISTRY_USERNAME:-${ALI_MALAYSIA_REGISTRY_USERNAME:-dcc_kevin@5533279936379346.onaliyun.com}}"
REGISTRY_PASSWORD="${ALI_SINGAPORE_REGISTRY_PASSWORD:-${ALI_MALAYSIA_REGISTRY_PASSWORD:-}}"
IMAGE="$REGISTRY/dcc-cloud/zou-backend:0.0.3"

: "${REGISTRY_PASSWORD:?ALI_SINGAPORE_REGISTRY_PASSWORD is required}"

printf '%s' "$REGISTRY_PASSWORD" | docker login \
    --username="$REGISTRY_USERNAME" \
    --password-stdin \
    "$REGISTRY"

if [ "$LOGIN_ONLY" = true ]; then
    echo "Docker login succeeded for $REGISTRY."
    exit 0
fi

docker buildx build \
    --platform linux/amd64 \
    --provenance=false \
    --sbom=false \
    --output "type=image,name=$IMAGE,push=true,oci-mediatypes=true" \
    -f "$REPO_ROOT/Dockerfile" \
    "$REPO_ROOT"

cd "$SCRIPT_DIR"
s deploy --skip-push -y
