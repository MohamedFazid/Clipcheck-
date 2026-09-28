"""End-to-end latency of the running app, as a user meets it (added 2026-09-25).

scripts/benchmark_latency.py times each pipeline stage in one process on one clip. This script times the whole request path of
the live server (http://localhost:8000): POST /api/analyze, polling /api/progress every 0.1 s as the interface does, until the
result is ready, on each featured example clip (one per kind of result). It therefore includes what the stage benchmark leaves
out: the server's own work (face-crop image, waveform, out-of-domain checks, moment windows, explanation with timing, the
faithfulness screen and its template fallback) and polling granularity (up to 0.1 s).

The server must already be warm (models loaded); one untimed warm-up pass over all clips is run first. Jobs created here are
removed afterwards. Writes results/latency/app_end_to_end.json; an existing file is never overwritten without --overwrite.

    /opt/anaconda3/bin/python scripts/benchmark_app_latency.py --runs 3
"""
import argparse
import json
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'results' / 'latency' / 'app_end_to_end.json'


def time_one(base, demo_id):
    job = requests.post(f'{base}/api/demo/{demo_id}').json()
    t0 = time.perf_counter()
    requests.post(f'{base}/api/analyze/{job["id"]}')
    while True:
        p = requests.get(f'{base}/api/progress/{job["id"]}').json()
        if p['status'] in ('done', 'error'):
            break
        time.sleep(0.1)
    wall = time.perf_counter() - t0
    r = requests.get(f'{base}/api/result/{job["id"]}').json()
    requests.delete(f'{base}/api/queue/{job["id"]}')
    return wall, r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', default='http://localhost:8000')
    ap.add_argument('--runs', type=int, default=3)
    ap.add_argument('--overwrite', action='store_true')
    args = ap.parse_args()
    if OUT.exists() and not args.overwrite:
        raise SystemExit(f'{OUT} exists; archive it or pass --overwrite')
    try:
        demos = [d for d in requests.get(f'{args.base}/api/demo_clips', timeout=5).json() if d.get('featured') is not None]
    except requests.RequestException:
        raise SystemExit(f'Nothing is running at {args.base}; start the app first: ~/mdd/run_server.sh')
    demos.sort(key=lambda d: d['featured'])
    print(f'Warm-up pass over {len(demos)} clips (not timed)...', flush=True)
    for d in demos:
        time_one(args.base, d['demo_id'])
    rows = []
    for d in demos:
        times, last = [], None
        for _ in range(args.runs):
            t, last = time_one(args.base, d['demo_id'])
            times.append(t)
        exp = last.get('explanation') or {}
        rows.append({'clip': d['name'], 'title': d['title'], 'duration_s': d['duration'], 'verdict': last.get('verdict'),
                     'explanation_source': exp.get('source'), 'moments': len(last.get('anomalies') or []),
                     'faces': (last.get('video') or {}).get('n_faces'),
                     'mean_s': round(statistics.mean(times), 3), 'min_s': round(min(times), 3), 'max_s': round(max(times), 3),
                     'runs_s': [round(t, 3) for t in times]})
        print(f"  {d['name']:22s} {rows[-1]['verdict'] or '':22s} {rows[-1]['mean_s']:6.2f} s  (min {rows[-1]['min_s']:.2f}, max {rows[-1]['max_s']:.2f})", flush=True)
    with_face = [r['mean_s'] for r in rows if r['faces']]
    summary = {'measured_at': datetime.now().astimezone().isoformat(timespec='seconds'), 'base': args.base, 'runs_per_clip': args.runs,
               'warmup_passes': 1, 'poll_interval_s': 0.1, 'clips': rows,
               'mean_over_clips_s': round(statistics.mean(r['mean_s'] for r in rows), 3),
               'median_over_clips_s': round(statistics.median(r['mean_s'] for r in rows), 3),
               'max_clip_mean_s': max(r['mean_s'] for r in rows),
               'mean_over_clips_with_a_face_s': round(statistics.mean(with_face), 3) if with_face else None}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(summary, indent=2))
    print(f"mean over clips {summary['mean_over_clips_s']} s, median {summary['median_over_clips_s']} s, slowest clip "
          f"{summary['max_clip_mean_s']} s; wrote {OUT}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
