#!/usr/bin/env bash
# One-step setup: creates .venv, installs requirements-app.txt, downloads and verifies the model weights, offers Llama 3.
# Usage: ./setup.sh [--llm | --no-llm]   (PYTHON=/path/to/python3.12 picks the Python; safe to run again)
set -euo pipefail
cd "$(dirname "$0")"

LLM=ask
for arg in "$@"; do
  case "$arg" in
    --no-llm) LLM=no ;;
    --llm) LLM=yes ;;
    *) echo "Unknown option: $arg (use --llm or --no-llm)"; exit 2 ;;
  esac
done

# 1. Python environment -----------------------------------------------------------------------------------------------
# The pinned packages need Python 3.12 or newer (numpy 2.5.0); 3.12 is the tested version, so it is preferred.
py_version() { "$1" -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null; }
py_ok() { "$1" -c 'import sys; sys.exit(sys.version_info[:2] < (3, 12))' 2>/dev/null; }

if [ -x .venv/bin/python ] && ! py_ok .venv/bin/python; then
  echo "==> Removing .venv: it was made with Python $(py_version .venv/bin/python), and this project needs 3.12"
  rm -rf .venv
fi

if [ ! -x .venv/bin/python ]; then
  BASE_PY=""
  for cand in "${PYTHON:-}" python3.12 /opt/homebrew/bin/python3.12 /usr/local/bin/python3.12 \
              /opt/anaconda3/bin/python3.12 "$HOME/anaconda3/bin/python3.12" "$HOME/miniconda3/bin/python3.12" \
              /Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12 python3.13 python3; do
    [ -n "$cand" ] && command -v "$cand" >/dev/null 2>&1 && py_ok "$cand" && { BASE_PY="$cand"; break; }
  done
  if [ -z "$BASE_PY" ]; then
    echo "Python 3.12 not found (this project needs 3.12; 'python3' here is $(py_version python3 || echo 'missing'))."
    echo "Install it with 'brew install python@3.12' (macOS) or from https://www.python.org/downloads/, then run ./setup.sh again."
    echo "If it is installed somewhere else: PYTHON=/path/to/python3.12 ./setup.sh"
    exit 1
  fi
  VER="$(py_version "$BASE_PY")"
  if [ "$VER" != "3.12" ]; then echo "Note: using Python $VER; the project was tested with 3.12."; fi
  echo "==> Creating .venv with $BASE_PY (Python $VER)"
  "$BASE_PY" -m venv .venv
fi
PY=.venv/bin/python

echo "==> Installing the app requirements into .venv (several minutes the first time)"
"$PY" -m pip install --upgrade pip >/dev/null
if ! "$PY" -m pip install -r requirements-app.txt; then
  echo "Package install failed. Check your internet connection, then run ./setup.sh again."
  echo "If it keeps failing, start clean with Python 3.12: rm -rf .venv && PYTHON=/path/to/python3.12 ./setup.sh"
  exit 1
fi

# 2. Trained model weights --------------------------------------------------------------------------------------------
echo "==> Downloading and verifying the trained model weights"
"$PY" scripts/download_models.py

# 3. Optional: Llama 3 for the written explanations -------------------------------------------------------------------
# wav2vec2-base is fetched from Hugging Face automatically on the first analysis; MTCNN and Silero VAD come with pip.
if [ "$LLM" = ask ] && [ -t 0 ]; then
  read -r -p "Download Llama 3 8B (about 4.7 GB) for the written explanations? [y/N] " reply
  case "$reply" in [yY]*) LLM=yes ;; *) LLM=no ;; esac
fi
if [ "$LLM" = yes ]; then
  if command -v ollama >/dev/null 2>&1; then
    echo "==> Pulling llama3:8b with Ollama"
    ollama pull llama3:8b || echo "Could not pull llama3:8b. Start Ollama (ollama serve) and run: ollama pull llama3:8b"
  else
    echo "Ollama is not installed. Get it from https://ollama.com (macOS: brew install ollama), then run: ollama pull llama3:8b"
  fi
else
  echo "Skipping Llama 3. The app still works and shows the plain-language standard wording instead."
  echo "To add it later: install Ollama (https://ollama.com), then run: ollama pull llama3:8b"
fi

echo
echo "Setup complete. Start the app with ./run_server.sh and open http://localhost:8000"
echo "(for the written explanations, keep 'ollama serve' running in another terminal)."
