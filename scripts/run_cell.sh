#!/bin/bash
# One experiment cell: train.py then evaluate.py. Usage: scripts/run_cell.sh <tag> <seed> [train.py args...]
# Skips finished cells; a checkpoint without history.json is moved to models/runs/_partial/; steps are logged to results/logs/events.log.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1
PY="${PY:-/opt/anaconda3/bin/python}"
tag="$1"; seed="$2"; shift 2

run_dir="results/runs/$tag/seed$seed"
ckpt="models/runs/$tag/seed$seed.pth"
logdir="results/logs/$tag"
mkdir -p "$logdir"
events="results/logs/events.log"

if [ -f "$run_dir/metrics.json" ]; then
  echo "skip $tag seed$seed (already complete)"; exit 0
fi
if [ -f "$ckpt" ] && [ ! -f "$run_dir/history.json" ]; then
  mkdir -p models/runs/_partial
  mv "$ckpt" "models/runs/_partial/${tag}_seed${seed}_$(date +%Y%m%d%H%M%S).pth"
  echo "[$(date '+%F %T')] PARTIAL checkpoint moved aside: $tag seed$seed" >> "$events"
fi

echo "[$(date '+%F %T')] START $tag seed$seed args: $*" >> "$events"
"$PY" -u scripts/train.py --seed "$seed" --tag "$tag" "$@" > "$logdir/seed$seed.train.log" 2>&1
rc=$?
if [ $rc -ne 0 ]; then
  echo "[$(date '+%F %T')] FAIL train $tag seed$seed (exit $rc)" >> "$events"; exit $rc
fi
"$PY" -u scripts/evaluate.py --seed "$seed" --tag "$tag" --no-plots > "$logdir/seed$seed.eval.log" 2>&1
rc=$?
if [ $rc -ne 0 ]; then
  echo "[$(date '+%F %T')] FAIL eval $tag seed$seed (exit $rc)" >> "$events"; exit $rc
fi
echo "[$(date '+%F %T')] DONE $tag seed$seed" >> "$events"
