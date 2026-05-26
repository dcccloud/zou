#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [ -n "${CONDA_PREFIX:-}" ]; then
  export PATH="$CONDA_PREFIX/bin:$PATH"
elif [ -d ".venv" ]; then
  # shellcheck disable=SC1091
  source ".venv/bin/activate"
else
  echo "No conda environment is active and .venv is missing." >&2
  echo "Run: conda activate raven-zou" >&2
  echo "Or create .venv and install requirements there." >&2
  exit 1
fi

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

echo "Starting Zou API on http://${HOST}:${PORT}"
exec gunicorn \
  -k gevent \
  -w "$GUNICORN_WORKERS" \
  --bind "${HOST}:${PORT}" \
  --timeout "$GUNICORN_TIMEOUT" \
  --access-logfile - \
  --error-logfile - \
  zou.app:app
