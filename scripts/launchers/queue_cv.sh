#!/bin/bash
# 5-fold identity-grouped cross-validation of the leading candidate (Xception, multi-method), fixed seed 42, so results
# vary with the DATA partition. Waits for the ConvNeXt multi-method queue so two trainings never share the GPU.
# Idempotent via run_cell.sh. Output: results/cv/cv5_xcep_mm/cv_summary.md
ROOT="$(cd "$(dirname "$0")/../.." && pwd -P)"; cd "$ROOT" || exit 1
PY="${PY:-/opt/anaconda3/bin/python}"
until grep -q "QUEUE mm_convnext COMPLETE" results/logs/events.log; do sleep 60; done
mkdir -p results/logs/cv
for k in 0 1 2 3 4; do
  scripts/run_cell.sh "cv5_xcep_f$k" 42 --arch legacy_xception --frames-dir frames_multi --fold "$k" --epochs 10
done
"$PY" scripts/aggregate_cv.py --prefix cv5_xcep_f --name cv5_xcep_mm > results/logs/cv/aggregate.log 2>&1
echo "[$(date '+%F %T')] QUEUE cv5_xcep COMPLETE" >> results/logs/events.log
