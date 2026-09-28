#!/bin/bash
# Multi-method ConvNeXt-Tiny (best single-method backbone), same recipe as the other multi-method runs.
ROOT="$(cd "$(dirname "$0")/../.." && pwd -P)"; cd "$ROOT" || exit 1
PY="${PY:-/opt/anaconda3/bin/python}"
for seed in 42 43 44; do
  scripts/run_cell.sh mm_cnxt_vidsplit "$seed" --arch convnext_tiny --frames-dir frames_multi --epochs 10
done
"$PY" scripts/aggregate_runs.py --tag mm_cnxt_vidsplit > results/logs/multimethod/mm_cnxt_vidsplit.aggregate.log 2>&1
"$PY" scripts/eval_cross_method.py --tags mm_cnxt_vidsplit > results/logs/multimethod/cross_method_cnxt.log 2>&1
echo "[$(date '+%F %T')] QUEUE mm_convnext COMPLETE" >> results/logs/events.log
