#!/bin/bash
# Download FaceSwap and NeuralTextures (FF++ c23, first 200 videos) for the cross-method test.
# Usage: bash scripts/download_extra_methods.sh [EU2|EU|CA]   (asks you to accept the FF++ terms)
ROOT="$(cd "$(dirname "$0")/.." && pwd -P)"
PY=/opt/anaconda3/bin/python
SERVER="${1:-EU2}"
for m in FaceSwap NeuralTextures; do
  "$PY" "$ROOT/scripts/download_ff.py" "$ROOT/data" -d "$m" -c c23 -t videos -n 200 --server "$SERVER" \
    || { echo "Download of $m failed. Try: bash scripts/download_extra_methods.sh EU   (or CA)"; exit 1; }
done
echo "Both methods downloaded."
