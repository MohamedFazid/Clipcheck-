"""Evaluate the out-of-domain gates on every cached set, with and without the gate, against the ship criteria (ledger O1).

    python scripts/eval_ood_gate.py   # app env"""
import json
import sys
from collections import Counter
from pathlib import Path

import joblib
import numpy as np
from sklearn.metrics import roc_auc_score

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fusion import fuse  # noqa: E402
from ood_gate import clip_video_distance  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FEAT = ROOT / 'results' / 'ood_gate' / 'features'
SETS = ('heldout', 'fallback', 'lavdf', 'lavdf_dev', 'timit', 'celebdf', 'veo')
IN_DOMAIN = ('heldout', 'fallback')


def auc(y, p):
    return float(roc_auc_score(y, p)) if len(set(y)) == 2 else None


def outcome(rows, key):
    n = len(rows)
    verdicts = Counter(r[key] for r in rows)
    scored = [r for r in rows if r[key] != 'INCONCLUSIVE']
    correct = [r for r in scored if (r[key] in ('FAKE', 'PARTIAL_MANIPULATION')) == r['truth_fake']]
    out = {'n': n, 'verdicts': dict(verdicts), 'coverage': len(scored) / n if n else None,
           'accuracy_all_clips': len(correct) / n if n else None,
           'accuracy_on_answered': len(correct) / len(scored) if scored else None,
           'confident_wrong': len(scored) - len(correct)}
    for cat, mod in (('RVFA', 'audio'), ('FVRA', 'video')):
        sub = [r for r in rows if r.get('category') == cat]
        if sub:
            out[f'{cat}_names_{mod}'] = sum(1 for r in sub if r[key + '_implicated'] == mod) / len(sub)
    return out


def main():
    ag = joblib.load(ROOT / 'models' / 'audio_ood_gate.joblib')['gate']
    vg = joblib.load(ROOT / 'models' / 'video_ood_gate.joblib')['gate']
    report, per_clip = {'audio_gate': {'kind': ag.kind, 'threshold': ag.threshold_},
                        'video_gate': {'kind': vg.kind, 'threshold': vg.threshold_}, 'sets': {}}, {}
    for s in SETS:
        path = FEAT / f'{s}.joblib'
        if not path.exists():
            continue
        rows = []
        for r in joblib.load(path):
            a_lab = r['audio_label'] or ('bonafide' if s == 'celebdf' else None)
            x = {'set': s, 'id': r['id'], 'category': r['id'][:4] if r['id'][:4] in ('RVRA', 'RVFA', 'FVRA', 'FVFA') else
                 (r['id'].split('_')[1] if s == 'lavdf_dev' else None),
                 'video_label': r['video_label'], 'audio_label': a_lab, 'p_video': r['p_video'], 'p_audio': r['p_audio'],
                 'video_distance': None if r['video_features'] is None else clip_video_distance(vg, r['video_features'].astype(np.float32)),
                 'audio_distance': None if r['audio_embedding'] is None else float(ag.distance(r['audio_embedding'])[0])}
            x['video_ood'] = x['video_distance'] is not None and x['video_distance'] > vg.threshold_
            x['audio_ood'] = x['audio_distance'] is not None and x['audio_distance'] > ag.threshold_
            x['truth_fake'] = (x['video_label'] == 'fake') or (a_lab == 'spoof')
            for key, pv, pa in (('ungated', x['p_video'], x['p_audio']),
                                ('gated', None if x['video_ood'] else x['p_video'], None if x['audio_ood'] else x['p_audio'])):
                f = fuse(pv, pa)
                x[key], x[key + '_implicated'] = f.verdict, f.implicated_modality
            rows.append(x)
        with_v = [x for x in rows if x['video_distance'] is not None]
        with_a = [x for x in rows if x['audio_distance'] is not None]
        kept_a = [x for x in with_a if not x['audio_ood'] and x['audio_label']]
        kept_v = [x for x in with_v if not x['video_ood']]
        rep = {'n_clips': len(rows),
               'video_withheld': f'{sum(x["video_ood"] for x in with_v)}/{len(with_v)}',
               'audio_withheld': f'{sum(x["audio_ood"] for x in with_a)}/{len(with_a)}',
               'video_auc_all': auc([x['video_label'] == 'fake' for x in with_v], [x['p_video'] for x in with_v]),
               'video_auc_kept': auc([x['video_label'] == 'fake' for x in kept_v], [x['p_video'] for x in kept_v]),
               'audio_auc_all': auc([x['audio_label'] == 'spoof' for x in with_a if x['audio_label']],
                                    [x['p_audio'] for x in with_a if x['audio_label']]),
               'audio_auc_kept': auc([x['audio_label'] == 'spoof' for x in kept_a], [x['p_audio'] for x in kept_a])}
        if s != 'veo':
            rep['ungated'] = outcome(rows, 'ungated')
            rep['gated'] = outcome(rows, 'gated')
        report['sets'][s] = rep
        per_clip[s] = rows

    ind = [x for s in IN_DOMAIN for x in per_clip.get(s, [])]
    va = [x for x in ind if x['video_distance'] is not None]
    aa = [x for x in ind if x['audio_distance'] is not None]
    v_rate = sum(x['video_ood'] for x in va) / len(va)
    a_rate = sum(x['audio_ood'] for x in aa) / len(aa)
    h, l = report['sets']['heldout'], report['sets']['lavdf']
    drop = (h['ungated']['accuracy_all_clips'] - h['gated']['accuracy_all_clips']) * 100
    report['criteria'] = {
        'a_in_domain_abstention_video': v_rate, 'a_video_passes': v_rate <= 0.05,
        'a_in_domain_abstention_audio': a_rate, 'a_audio_passes': a_rate <= 0.05,
        'b_heldout_accuracy_drop_pp': drop, 'b_passes': drop <= 2.0,
        'c_lavdf_confident_wrong': [l['ungated']['confident_wrong'], l['gated']['confident_wrong']],
        'c_passes': l['gated']['confident_wrong'] < l['ungated']['confident_wrong']}
    out = ROOT / 'results' / 'ood_gate'
    json.dump(report, open(out / 'eval_report.json', 'w'), indent=1)
    joblib.dump(per_clip, out / 'per_clip.joblib')
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
