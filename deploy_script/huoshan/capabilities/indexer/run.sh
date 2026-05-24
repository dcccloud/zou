#!/usr/bin/env bash
set -euo pipefail

cd /opt/application

exec gunicorn \
    -k gevent \
    -w "${GUNICORN_WORKERS:-1}" \
    --bind "0.0.0.0:${PORT:-8000}" \
    --timeout "${GUNICORN_TIMEOUT:-600}" \
    --access-logfile - \
    --error-logfile - \
    zou.faas_capabilities.indexer.app:app
