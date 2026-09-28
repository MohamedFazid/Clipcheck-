"""Build frames_multi/: a class-balanced, multi-method training folder made of symlinks.

Layout (ImageFolder-compatible, identical video-folder names to frames/, so the frozen split applies):
    frames_multi/real/<id>   -> frames/real/<id>
    frames_multi/fake/<a_b>  -> frames/fake/<a_b>                     (Deepfakes)
                             or frames_methods/FaceSwap/<a_b>
                             or frames_methods/NeuralTextures/<a_b>

Each fake pair-direction <a_b> is assigned exactly ONE method, cycling through the methods within each split
(after a seeded shuffle), so real:fake stays 1:1 and each method contributes about one third of the fakes in
train, val and test. A model therefore sees every method but never the same clip in two versions. Test-split
identities are unseen in training whichever method they use.

The assignment is written to data_splits/multimethod_assignment_v1.json (tracked) for provenance.

    /opt/anaconda3/bin/python scripts/build_multimethod_frames.py
"""
import json
import os
import random
import shutil
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import PROJECT_ROOT, SPLIT_MANIFEST  # noqa: E402

METHODS = ['Deepfakes', 'FaceSwap', 'NeuralTextures']
SEED = 42
OUT = PROJECT_ROOT / 'frames_multi'


def source_dir(method, pair):
    if method == 'Deepfakes':
        return PROJECT_ROOT / 'frames' / 'fake' / pair
    return PROJECT_ROOT / 'frames_methods' / method / pair


def main():
    assign = json.load(open(SPLIT_MANIFEST))['assignment']
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / 'real').mkdir(parents=True)
    (OUT / 'fake').mkdir(parents=True)

    for key in sorted(k for k in assign if k.startswith('real/')):
        vid = key.split('/', 1)[1]
        os.symlink(os.path.relpath(PROJECT_ROOT / 'frames' / 'real' / vid, OUT / 'real'), OUT / 'real' / vid)

    rng = random.Random(SEED)
    chosen = {}
    for split in ('train', 'val', 'test'):
        pairs = sorted(k.split('/', 1)[1] for k, v in assign.items() if k.startswith('fake/') and v == split)
        rng.shuffle(pairs)
        for i, pair in enumerate(pairs):
            chosen[pair] = METHODS[i % len(METHODS)]

    for pair, method in sorted(chosen.items()):
        src = source_dir(method, pair)
        if not src.exists() or not any(src.glob('*.jpg')):
            sys.exit(f'missing crops for {method}/{pair}: run scripts/launchers/queue_extract_methods.sh first')
        os.symlink(os.path.relpath(src, OUT / 'fake'), OUT / 'fake' / pair)

    summary = {s: dict(Counter(chosen[p] for p, _ in [(k.split('/', 1)[1], v) for k, v in assign.items()
                                                      if k.startswith('fake/') and v == s]))
               for s in ('train', 'val', 'test')}
    json.dump({'seed': SEED, 'methods': METHODS, 'method_per_pair': dict(sorted(chosen.items())),
               'counts_per_split': summary}, open(PROJECT_ROOT / 'data_splits' / 'multimethod_assignment_v1.json', 'w'),
              indent=1)
    n_real = len(list((OUT / 'real').iterdir()))
    n_fake = len(list((OUT / 'fake').iterdir()))
    crops = {c: sum(f.endswith('.jpg') for _, _, fs in os.walk(OUT / c, followlinks=True) for f in fs)
             for c in ('real', 'fake')}
    print(f'frames_multi: {n_real} real videos, {n_fake} fake videos | crops {crops}')
    print('fake methods per split:', summary)


if __name__ == '__main__':
    main()
