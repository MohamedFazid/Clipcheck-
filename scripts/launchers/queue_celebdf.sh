#!/bin/bash
# Cross-dataset (Celeb-DF-v2 official test list, 518 videos) for the finalists. Waits for the ConvNeXt multi-method
# queue. The seed of each tag is the one with the best VALIDATION accuracy (never chosen on test).
# Needs the deepfake-detect env (MTCNN).  Output: results/cross_dataset/celebdf_v2__<tag>/
ROOT="$(cd "$(dirname "$0")/../.." && pwd -P)"; cd "$ROOT" || exit 1
PYE=/opt/anaconda3/envs/deepfake-detect/bin/python
CELEB="${CELEBDF_ROOT:-$HOME/Downloads/Celeb-DF-v2}"   # Celeb-DF-v2 folder
until grep -q "QUEUE mm_convnext COMPLETE" results/logs/events.log; do sleep 60; done
for spec in "mm_xcep_vidsplit legacy_xception" "mm_cnxt_vidsplit convnext_tiny" "cnxt_vidsplit convnext_tiny"; do
  set -- $spec; tag=$1; arch=$2
  seed=$(/opt/anaconda3/bin/python - "$tag" <<'PY'
import json, sys
import numpy as np
tag = sys.argv[1]
best = max((max(json.load(open(f'results/runs/{tag}/seed{s}/history.json'))['val_acc']), s) for s in (42, 43, 44))
print(best[1])
PY
)
  out="celebdf_v2__${tag}"
  [ -f "results/cross_dataset/$out/metrics.json" ] && { echo "skip $out"; continue; }
  echo "[$(date '+%F %T')] START celebdf $tag seed$seed" >> results/logs/events.log
  "$PYE" -u scripts/eval_celebdf.py --root "$CELEB" --model "models/runs/$tag/seed$seed.pth" --arch "$arch" \
      --out-name "$out" > "results/logs/celebdf_$tag.log" 2>&1
  echo "[$(date '+%F %T')] DONE celebdf $tag seed$seed (exit $?)" >> results/logs/events.log
done
echo "[$(date '+%F %T')] QUEUE celebdf COMPLETE" >> results/logs/events.log
