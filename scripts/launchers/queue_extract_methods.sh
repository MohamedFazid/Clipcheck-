#!/bin/bash
# Extract MTCNN face crops for all videos of the extra FF++ methods into frames_methods/<Method>/ (app env).
ROOT="$(cd "$(dirname "$0")/../.." && pwd -P)"; cd "$ROOT" || exit 1
PYE=/opt/anaconda3/envs/deepfake-detect/bin/python
for m in FaceSwap NeuralTextures; do
  echo "[$(date '+%F %T')] extract $m start" >> results/logs/events.log
  "$PYE" scripts/extract_frames.py --fake-method "$m" --fake-only --out-root "frames_methods/$m" \
    > "results/logs/extract_$m.log" 2>&1
  echo "[$(date '+%F %T')] extract $m done (exit $?)" >> results/logs/events.log
done
