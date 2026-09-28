#!/bin/bash
# Finish the regularised variant on the identity-disjoint split, then summarise.
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT" || exit 1
PY="${PY:-/opt/anaconda3/bin/python}"
REG="--dropout 0.3 --label-smoothing 0.1 --early-stopping-patience 3 --epochs 10"
for seed in 42 43 44; do
  scripts/run_cell.sh reg_vidsplit "$seed" $REG
done
"$PY" scripts/aggregate_runs.py --tag reg_vidsplit > results/logs/reg_vidsplit/aggregate.log 2>&1
"$PY" scripts/compare_variants.py --variants base_vidsplit aug_vidsplit reg_vidsplit \
  --baseline-tag base_vidsplit --out-name variant_comparison_vidsplit > results/logs/reg_vidsplit/compare.log 2>&1
echo "[$(date '+%F %T')] QUEUE reg_resume COMPLETE" >> results/logs/events.log
