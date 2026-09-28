#!/usr/bin/env bash
# Launches the FastAPI + vanilla JS/CSS frontend (server.py + static/).
cd "$(dirname "$0")"
exec /opt/anaconda3/envs/deepfake-detect/bin/python -m uvicorn server:app --host 0.0.0.0 --port 8000 "$@"
