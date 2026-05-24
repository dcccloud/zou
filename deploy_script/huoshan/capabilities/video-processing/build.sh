#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export CAPABILITY_NAME="video-processing"
export CAPABILITY_MODULE="zou.faas_capabilities.video_processing.app"
export CAPABILITY_IMAGE_REPOSITORY="${CAPABILITY_IMAGE_REPOSITORY:-dcc-cloud2-cn-beijing.cr.volces.com/dcc-cloud/zou-capability-video-processing}"
export CAPABILITY_DIR="$SCRIPT_DIR"
export CAPABILITY_APIG_GATEWAY_ID="${VIDEO_PROCESSING_APIG_GATEWAY_ID:-${CAPABILITY_APIG_GATEWAY_ID:-${DEV_APIG_GATEWAY_ID:-}}}"

"$SCRIPT_DIR/../_common/build-capability.sh"
