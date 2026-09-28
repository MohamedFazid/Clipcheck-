#!/bin/bash
# Multi-method EfficientNet-B4 (the PPR architecture), same recipe as the other multi-method runs;
# judged by the ship rule frozen in docs/EXPERIMENTS.md (V14).
ROOT="$(cd "$(dirname "$0")/../.." && pwd -P)"; cd "$ROOT" || exit 1
PY="${PY:-/opt/anaconda3/bin/python}"
mkdir -p results/logs/multimethod
for seed in 42 43 44; do
  scripts/run_cell.sh mm_b4_vidsplit "$seed" --arch efficientnet_b4 --frames-dir frames_multi --epochs 10
done
"$PY" scripts/aggregate_runs.py --tag mm_b4_vidsplit > results/logs/multimethod/mm_b4_vidsplit.aggregate.log 2>&1
"$PY" scripts/eval_cross_method.py --tags mm_b4_vidsplit > results/logs/multimethod/cross_method_b4.log 2>&1
echo "[$(date '+%F %T')] QUEUE mm_b4 COMPLETE" >> results/logs/events.log
