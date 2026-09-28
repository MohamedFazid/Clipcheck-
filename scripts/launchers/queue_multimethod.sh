#!/bin/bash
# Multi-method training (Deepfakes + FaceSwap + NeuralTextures) for the leading backbones, same recipe as the bake-off.
# Waits for the bake-off queue so the GPU is never shared.
ROOT="$(cd "$(dirname "$0")/../.." && pwd -P)"; cd "$ROOT" || exit 1
PY="${PY:-/opt/anaconda3/bin/python}"
until grep -q "QUEUE bakeoff_video COMPLETE" results/logs/events.log; do sleep 60; done
mkdir -p results/logs/multimethod
for spec in "mm_r50_vidsplit resnet50" "mm_xcep_vidsplit legacy_xception" "mm_b0_vidsplit efficientnet_b0"; do
  set -- $spec; tag=$1; arch=$2
  for seed in 42 43 44; do
    scripts/run_cell.sh "$tag" "$seed" --arch "$arch" --frames-dir frames_multi --epochs 10
  done
  "$PY" scripts/aggregate_runs.py --tag "$tag" > "results/logs/multimethod/$tag.aggregate.log" 2>&1
done
"$PY" scripts/eval_cross_method.py --tags mm_r50_vidsplit mm_xcep_vidsplit mm_b0_vidsplit cnxt_vidsplit \
  > results/logs/multimethod/cross_method.log 2>&1
"$PY" scripts/compare_variants.py --variants mm_r50_vidsplit mm_xcep_vidsplit mm_b0_vidsplit \
  --baseline-tag mm_r50_vidsplit --out-name multimethod_vidsplit > results/logs/multimethod/compare.log 2>&1
echo "[$(date '+%F %T')] QUEUE multimethod COMPLETE" >> results/logs/events.log
