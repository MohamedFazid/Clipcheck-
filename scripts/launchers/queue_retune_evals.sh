#!/bin/bash
# Re-runs the two fusion evaluations at the re-tuned T = 0.35 (the earlier pass used T = 0.30, kept as *_T030).
# Waits for the shipped-evals queue so two jobs never share the GPU.
ROOT="$(cd "$(dirname "$0")/../.." && pwd -P)"; cd "$ROOT" || exit 1
PY="${PY:-/opt/anaconda3/bin/python}"
APP="${APP:-/opt/anaconda3/envs/deepfake-detect/bin/python}"
ev=results/logs/events.log
log(){ echo "[$(date '+%F %T')] $*" >> "$ev"; }
until grep -q "QUEUE shipped_evals COMPLETE" "$ev"; do sleep 30; done
mkdir -p results/logs/shipped_evals

T=$("$PY" -c "import sys; sys.path.insert(0,'scripts'); from fusion import THRESHOLD_T_DEFAULT as t; print(t)")
log "RETUNE-EVALS start (T = $T)"

for pair in "fallback_eval_shipped:eval_fallback/manifest.json" "hybrid_eval_shipped:eval_hybrid/manifest.json"; do
  out="${pair%%:*}"; man="${pair##*:}"
  [ -d "results/$out" ] && [ ! -d "results/${out}_T030" ] && mv "results/$out" "results/${out}_T030"
  log "$out re-run at T=$T start"
  "$APP" -u scripts/eval_fallback_4condition.py --manifest "$man" --out-dir "results/$out" \
    > "results/logs/shipped_evals/${out}_retuned.log" 2>&1
  log "$out re-run done (exit $?)"
done

"$PY" scripts/build_numbers.py > results/logs/shipped_evals/build_numbers_retuned.log 2>&1
log "QUEUE retune_evals COMPLETE"
