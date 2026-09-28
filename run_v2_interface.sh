#!/usr/bin/env bash
# Runs the frozen v2 interface (round 2 of user testing) on port 8002, with the same backend and models.
# Can run alongside ./run_server.sh (it loads its own copy of the models).
cd "$(dirname "$0")"
export DEEPFAKE_STATIC_DIR="$PWD/docs/user_testing/ui_v2_snapshot"
source scripts/app_python.sh
"$PY" scripts/download_models.py --if-missing || exit 1   # fetch the weights on first run
exec "$PY" -m uvicorn server:app --host 127.0.0.1 --port 8002 "$@"
