#!/usr/bin/env bash
# Runs the ORIGINAL interface (v1, frozen 2026-09-24 before user testing) on port 8001, with the same backend and models as the
# normal app. For screenshots of the old interface in the report after the redesign. The normal app (./run_server.sh, port 8000)
# is unaffected; both can run at once (the second one loads its own copy of the models).
cd "$(dirname "$0")"
export DEEPFAKE_STATIC_DIR="$PWD/docs/user_testing/ui_v1_snapshot"
exec /opt/anaconda3/envs/deepfake-detect/bin/python -m uvicorn server:app --host 127.0.0.1 --port 8001 "$@"
