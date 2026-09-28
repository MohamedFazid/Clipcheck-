#!/usr/bin/env bash
# Launches the FastAPI + vanilla JS/CSS frontend (server.py + static/).
cd "$(dirname "$0")"
source scripts/app_python.sh
"$PY" scripts/download_models.py --if-missing || exit 1   # fetch the weights on first run
exec "$PY" -m uvicorn server:app --host 0.0.0.0 --port 8000 "$@"
