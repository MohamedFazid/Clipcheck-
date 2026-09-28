#!/usr/bin/env bash
# Runs the interface v2 "Clipcheck" (frozen 2026-09-26 21:03, the version round 2 of user testing used) on port 8002, with the same backend and models as the
# normal app. For screenshots of v2 in the report after the v3 redesign. The normal app (./run_server.sh, port 8000)
# is unaffected; both can run at once (the second one loads its own copy of the models).
cd "$(dirname "$0")"
export DEEPFAKE_STATIC_DIR="$PWD/docs/user_testing/ui_v2_snapshot"
exec /opt/anaconda3/envs/deepfake-detect/bin/python -m uvicorn server:app --host 127.0.0.1 --port 8002 "$@"
