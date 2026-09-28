#!/bin/bash
# Re-runs every evaluation that consumed the video model, now that a model is shipped.
# Sequential on purpose: each step loads the model on the GPU, and latency is meaningless if anything else is running.
# Outputs go to *_shipped folders, which build_numbers.py reads, so the app's Evaluation tab fills in by itself.
# The superseded results stay untouched in results/OLD_model/ and results/{fallback_eval,hybrid_eval,latency}/.
ROOT="$(cd "$(dirname "$0")/../.." && pwd -P)"; cd "$ROOT" || exit 1
PY="${PY:-/opt/anaconda3/bin/python}"
APP="${APP:-/opt/anaconda3/envs/deepfake-detect/bin/python}"
ev=results/logs/events.log
log(){ echo "[$(date '+%F %T')] $*" >> "$ev"; }
mkdir -p results/logs/shipped_evals

log "SHIPPED-EVALS start (model: $(${PY} -c "import json;m=json.load(open('models/shipped_model.json'));print(m['tag'],'seed',m['seed'],m['arch'])"))"

log "four-condition start"
"$APP" -u scripts/eval_fallback_4condition.py --out-dir results/fallback_eval_shipped \
  > results/logs/shipped_evals/four_condition.log 2>&1
log "four-condition done (exit $?)"

log "threshold tuning start"
"$PY" -u scripts/tune_threshold_fallback.py --results results/fallback_eval_shipped/fallback_4condition_results.json \
  --out results/fallback_eval_shipped/threshold_tuning.json > results/logs/shipped_evals/threshold.log 2>&1
log "threshold tuning done (exit $?)"

log "hybrid start"
"$APP" -u scripts/eval_fallback_4condition.py --manifest eval_hybrid/manifest.json --out-dir results/hybrid_eval_shipped \
  > results/logs/shipped_evals/hybrid.log 2>&1
log "hybrid done (exit $?)"

log "preprocessing parity start"
"$APP" -u scripts/check_preprocessing_parity.py --tag mm_xcep_vidsplit --seed 44 \
  > results/logs/shipped_evals/parity.log 2>&1
log "preprocessing parity done (exit $?)"

log "latency start"
"$APP" -u scripts/benchmark_latency.py --runs 3 --overwrite \
  > results/logs/shipped_evals/latency.log 2>&1
log "latency done (exit $?)"

"$PY" scripts/build_numbers.py > results/logs/shipped_evals/build_numbers.log 2>&1
log "QUEUE shipped_evals COMPLETE"
