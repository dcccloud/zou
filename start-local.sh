#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

APP_PROFILE="${1:-${ZOU_APP_PROFILE:-full}}"
case "$APP_PROFILE" in
  full|faas|capability) ;;
  *)
    echo "Unsupported profile: $APP_PROFILE" >&2
    echo "Usage: $0 [full|faas|capability]" >&2
    exit 1
    ;;
esac

CONDA_BASE="$(conda info --base 2>/dev/null || true)"
ZOU_CONDA_ENV="${ZOU_CONDA_ENV:-}"
if [ -z "$ZOU_CONDA_ENV" ] && [ -n "$CONDA_BASE" ] && [ -d "$CONDA_BASE/envs/raven-zou" ]; then
  ZOU_CONDA_ENV="raven-zou"
fi

if [ -n "$ZOU_CONDA_ENV" ] && [ -n "$CONDA_BASE" ] && [ -d "$CONDA_BASE/envs/$ZOU_CONDA_ENV" ]; then
  export PATH="$CONDA_BASE/envs/$ZOU_CONDA_ENV/bin:$PATH"
elif [ -n "${CONDA_PREFIX:-}" ] && [ "${CONDA_DEFAULT_ENV:-}" != "base" ]; then
  export PATH="$CONDA_PREFIX/bin:$PATH"
elif [ -d ".venv" ]; then
  # shellcheck disable=SC1091
  source ".venv/bin/activate"
else
  echo "No usable conda environment or .venv was found." >&2
  echo "Run: conda activate raven-zou" >&2
  echo "Or create .venv and install requirements there." >&2
  exit 1
fi

export ZOU_APP_PROFILE="$APP_PROFILE"
export HOST="${HOST:-127.0.0.1}"
export PORT="${PORT:-5010}"
export DEBUG="${DEBUG:-True}"
export DOMAIN_NAME="${DOMAIN_NAME:-localhost:${PORT}}"
export DOMAIN_PROTOCOL="${DOMAIN_PROTOCOL:-http}"
export MAIL_ENABLED="${MAIL_ENABLED:-False}"
export ENABLE_JOB_QUEUE="${ENABLE_JOB_QUEUE:-False}"
export FS_BACKEND="${FS_BACKEND:-local}"
export PREVIEW_FOLDER="${PREVIEW_FOLDER:-/tmp/previews}"
export TMP_DIR="${TMP_DIR:-/tmp/zou}"
export GUNICORN_WORKERS="${GUNICORN_WORKERS:-1}"
export GUNICORN_TIMEOUT="${GUNICORN_TIMEOUT:-600}"

if [ "$ZOU_APP_PROFILE" = "faas" ]; then
  export KV_CAPABILITY_JOBS_DB_INDEX="${KV_CAPABILITY_JOBS_DB_INDEX:-15}"
  export FAAS_CAPABILITY_INDEXER_URL="${FAAS_CAPABILITY_INDEXER_URL:-https://sd86mim923h0slf5sfavg.apigateway-cn-beijing.volceapi.com}"
  export FAAS_CAPABILITY_PLAYLIST_BUILD_URL="${FAAS_CAPABILITY_PLAYLIST_BUILD_URL:-https://sd86ml0sl0ar2klupd21g.apigateway-cn-beijing.volceapi.com}"
  export FAAS_CAPABILITY_VIDEO_PROCESSING_URL="${FAAS_CAPABILITY_VIDEO_PROCESSING_URL:-https://sd86mmkcl0ar2klupd4t0.apigateway-cn-beijing.volceapi.com}"
  export FAAS_CAPABILITY_TRIGGER_TIMEOUT="${FAAS_CAPABILITY_TRIGGER_TIMEOUT:-3}"
  export FAAS_CAPABILITY_TRIGGER_BATCH_SIZE="${FAAS_CAPABILITY_TRIGGER_BATCH_SIZE:-20}"
fi

mkdir -p "$PREVIEW_FOLDER" "$TMP_DIR"

python - <<'PY'
import importlib.util
import os
import sys
from pathlib import Path

missing = [name for name in ("gunicorn", "gevent") if importlib.util.find_spec(name) is None]
if missing:
    print(
        "Missing Python dependencies: %s\n"
        "Run:\n"
        "  python3 -m venv .venv\n"
        "  source .venv/bin/activate\n"
        "  pip install -r requirements.txt" % ", ".join(missing),
        file=sys.stderr,
    )
    sys.exit(1)

if not Path(".env").is_file() and not os.getenv("DB_HOST"):
    print(
        "Warning: .env not found and DB_HOST is not set. "
        "Zou will fall back to localhost PostgreSQL/Redis defaults.",
        file=sys.stderr,
    )
PY

echo "Starting Zou API (${ZOU_APP_PROFILE}) on http://${HOST}:${PORT}"
exec gunicorn \
  -k gevent \
  -w "$GUNICORN_WORKERS" \
  --bind "${HOST}:${PORT}" \
  --timeout "$GUNICORN_TIMEOUT" \
  --access-logfile - \
  --error-logfile - \
  zou.app:app
