# Sourced by the run_*.sh launchers and setup.sh: sets $PY to the app environment's Python.
# First match wins: $PYTHON, the .venv made by ./setup.sh, the developer's conda environment, then python3.
if [ -n "${PYTHON:-}" ]; then
  PY="$PYTHON"
elif [ -x .venv/bin/python ]; then
  PY=.venv/bin/python
elif [ -x /opt/anaconda3/envs/deepfake-detect/bin/python ]; then
  PY=/opt/anaconda3/envs/deepfake-detect/bin/python
else
  PY=python3
fi
