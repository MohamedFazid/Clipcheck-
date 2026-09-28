#!/usr/bin/env bash
# Runs the frozen v1 interface (round 1 of user testing) on port 8001, with the same backend and models.
# Can run alongside ./run_server.sh (it loads its own copy of the models).
cd "$(dirname "$0")"
export DEEPFAKE_STATIC_DIR="$PWD/docs/user_testing/ui_v1_snapshot"
source scripts/app_python.sh
"$PY" scripts/download_models.py --if-missing || exit 1   # fetch the weights on first run
exec "$PY" -m uvicorn server:app --host 127.0.0.1 --port 8001 "$@"
