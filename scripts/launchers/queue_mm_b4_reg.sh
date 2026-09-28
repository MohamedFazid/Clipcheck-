#!/bin/bash
# Regularised multi-method EfficientNet-B4 (dropout 0.3, label smoothing 0.1, early stopping 3), judged by the same ship rule.
# Waits for queue_mm_b4.sh so two trainings never share the GPU.
ROOT="$(cd "$(dirname "$0")/../.." && pwd -P)"; cd "$ROOT" || exit 1
PY="${PY:-/opt/anaconda3/bin/python}"
until grep -q "QUEUE mm_b4 COMPLETE" results/logs/events.log; do sleep 60; done
mkdir -p results/logs/multimethod
for seed in 42 43 44; do
  scripts/run_cell.sh mm_b4reg_vidsplit "$seed" --arch efficientnet_b4 --frames-dir frames_multi --epochs 10 \
    --dropout 0.3 --label-smoothing 0.1 --early-stopping-patience 3
done
"$PY" scripts/aggregate_runs.py --tag mm_b4reg_vidsplit > results/logs/multimethod/mm_b4reg_vidsplit.aggregate.log 2>&1
"$PY" scripts/eval_cross_method.py --tags mm_b4reg_vidsplit > results/logs/multimethod/cross_method_b4reg.log 2>&1
echo "[$(date '+%F %T')] QUEUE mm_b4reg COMPLETE" >> results/logs/events.log
