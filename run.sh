#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

# gthread instead of gevent: psycopg's C-level waits block gevent's event
# loop, so requests pinned to a busy worker stall for seconds while other
# workers sit idle. Threads block independently and gunicorn only hands a
# connection to a worker with a free thread.
exec gunicorn \
    -k gthread \
    -w "${GUNICORN_WORKERS:-8}" \
    --threads "${GUNICORN_THREADS:-4}" \
    --bind "0.0.0.0:${PORT:-8000}" \
    --timeout "${GUNICORN_TIMEOUT:-600}" \
    --access-logfile - \
    --access-logformat '%(h)s "%(r)s" %(s)s %(M)sms' \
    --error-logfile - \
    zou.app:app
