#!/bin/bash
# Video-backbone bake-off on the identity-disjoint split: same recipe as aug_vidsplit, only --arch varies.
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"; cd "$ROOT" || exit 1
PY="${PY:-/opt/anaconda3/bin/python}"
mkdir -p results/logs/bakeoff_video
for spec in "b0_vidsplit efficientnet_b0" "r50_vidsplit resnet50" "xcep_vidsplit legacy_xception" "cnxt_vidsplit convnext_tiny"; do
  set -- $spec; tag=$1; arch=$2
  for seed in 42 43 44; do
    scripts/run_cell.sh "$tag" "$seed" --arch "$arch" --epochs 10
  done
  "$PY" scripts/aggregate_runs.py --tag "$tag" > "results/logs/bakeoff_video/$tag.aggregate.log" 2>&1
done
"$PY" scripts/compare_variants.py --variants aug_vidsplit b0_vidsplit r50_vidsplit xcep_vidsplit cnxt_vidsplit \
  --baseline-tag aug_vidsplit --out-name bakeoff_video_vidsplit > results/logs/bakeoff_video/compare.log 2>&1
echo "[$(date '+%F %T')] QUEUE bakeoff_video COMPLETE" >> results/logs/events.log
