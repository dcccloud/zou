#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

exec gunicorn \
    -k gevent \
    -w "${GUNICORN_WORKERS:-2}" \
    --bind "0.0.0.0:${PORT:-8000}" \
    --timeout "${GUNICORN_TIMEOUT:-600}" \
    --access-logfile - \
    --error-logfile - \
    zou.app:app
