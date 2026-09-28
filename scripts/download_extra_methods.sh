#!/bin/bash
# Download two extra FaceForensics++ manipulation methods (c23, first 200 videos, which are the same
# identity pairs as the Deepfakes set) for the cross-method test.
# Run this yourself: the FF++ download script asks you to accept the FaceForensics terms of use.
#   bash scripts/download_extra_methods.sh          # default server EU2
#   bash scripts/download_extra_methods.sh EU       # or CA, if a server times out
ROOT="$(cd "$(dirname "$0")/.." && pwd -P)"
PY=/opt/anaconda3/bin/python
SERVER="${1:-EU2}"
for m in FaceSwap NeuralTextures; do
  "$PY" "$ROOT/scripts/download_ff.py" "$ROOT/data" -d "$m" -c c23 -t videos -n 200 --server "$SERVER" \
    || { echo "Download of $m failed. Try: bash scripts/download_extra_methods.sh EU   (or CA)"; exit 1; }
done
echo "Both methods downloaded."
