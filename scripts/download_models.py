"""Download the four trained model files from the GitHub release into models/ and verify each SHA-256.

    python scripts/download_models.py [--check | --if-missing] [--base-url URL]"""
import argparse
import hashlib
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / 'models'

# Set to "<owner>/<repo>" once the GitHub repository exists, so a ZIP download (which has no git remote) still works.
GITHUB_REPO = 'MohamedFazid/Clipcheck-'
RELEASE_TAG = 'v1.0'

# name -> (SHA-256, size in bytes); must match models/README.md (tests/test_download_models.py checks this).
MODEL_FILES = {
    'best_model.pth': ('fdd60748dc1c18441d493fc01ee8eb3e9028e7a5c75a938a79cf846062a75bd4', 83545469),
    'audio_spoof_svm.joblib': ('fcdea45879c5ddd79f2263c9fb09906a04f4cb33a1167140e21547618845b2fc', 11639757),
    'video_ood_gate.joblib': ('b8327604346fb0da64f790f3067c721ac80dfd1379fd5d93a3be076f28a198d0', 16819126),
    'audio_ood_gate.joblib': ('a4e0bf372eff9e838a29f5ed6a2f01b53d3dfb34252c17c580cb3a83d051ed4a', 2375556),
}


def sha256_of(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(chunk), b''):
            h.update(block)
    return h.hexdigest()


def repo_from_git_remote():
    """'<owner>/<repo>' from the origin remote if it points at GitHub, else None."""
    try:
        url = subprocess.run(['git', '-C', str(PROJECT_ROOT), 'remote', 'get-url', 'origin'],
                             capture_output=True, text=True, timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None
    m = re.search(r'github\.com[:/]([^/]+/[^/]+?)(?:\.git)?/?$', url)
    return m.group(1) if m else None


def resolve_base_url(cli_url=None):
    if cli_url:
        return cli_url.rstrip('/')
    if os.environ.get('DEEPFAKE_MODELS_URL'):
        return os.environ['DEEPFAKE_MODELS_URL'].rstrip('/')
    repo = GITHUB_REPO or repo_from_git_remote()
    if not repo:
        return None
    return f'https://github.com/{repo}/releases/download/{RELEASE_TAG}'


def download(url, dest, expected_size=None):
    """Stream url to dest, printing progress. Raises urllib.error.URLError / HTTPError on failure."""
    req = urllib.request.Request(url, headers={'User-Agent': 'multimodal-deepfake-detector'})
    with urllib.request.urlopen(req, timeout=60) as resp, open(dest, 'wb') as out:
        total = int(resp.headers.get('Content-Length') or expected_size or 0)
        done = 0
        while True:
            block = resp.read(1 << 20)
            if not block:
                break
            out.write(block)
            done += len(block)
            if total and sys.stdout.isatty():
                print(f'\r    {done / 1e6:6.1f} / {total / 1e6:.1f} MB', end='', flush=True)
    if total and sys.stdout.isatty():
        print()


def fetch_one(name, base_url, models_dir):
    """Download one file to a .part file, verify it, then move it into place. Returns True on success."""
    sha, size = MODEL_FILES[name]
    dest = models_dir / name
    part = models_dir / (name + '.part')
    url = f'{base_url}/{name}'
    print(f'  downloading {name} ({size / 1e6:.1f} MB) from {url}')
    try:
        download(url, part, size)
    except urllib.error.HTTPError as e:
        print(f'  FAILED {name}: HTTP {e.code} ({e.reason}). Is release {RELEASE_TAG} published with this file attached?')
        part.unlink(missing_ok=True)
        return False
    except (urllib.error.URLError, OSError) as e:
        print(f'  FAILED {name}: {e}')
        part.unlink(missing_ok=True)
        return False
    got = sha256_of(part)
    if got != sha:
        print(f'  FAILED {name}: checksum mismatch (expected {sha[:12]}..., got {got[:12]}...); download discarded')
        part.unlink(missing_ok=True)
        return False
    part.replace(dest)
    print(f'  ok  {name}')
    return True


def check_all(models_dir):
    """Return the names of files that are missing or whose checksum is wrong."""
    bad = []
    for name, (sha, _) in MODEL_FILES.items():
        path = models_dir / name
        if not path.exists():
            print(f'  missing   {name}')
            bad.append(name)
        elif sha256_of(path) != sha:
            print(f'  WRONG     {name} (checksum does not match models/README.md)')
            bad.append(name)
        else:
            print(f'  verified  {name}')
    return bad


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument('--check', action='store_true', help='verify only, download nothing')
    mode.add_argument('--if-missing', action='store_true', help='download only absent files, skip hashing present ones')
    ap.add_argument('--base-url', help='folder URL holding the files (overrides the GitHub release)')
    ap.add_argument('--models-dir', type=Path, default=MODELS_DIR, help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    models_dir = args.models_dir

    if args.if_missing:
        todo = [n for n in MODEL_FILES if not (models_dir / n).exists()]
        if not todo:
            return 0
        print('Model weights missing: ' + ', '.join(todo))
    else:
        print(f'Checking model weights in {models_dir}')
        todo = check_all(models_dir)
        if not todo:
            print('All model weights present and verified.')
            return 0
        if args.check:
            print(f'{len(todo)} file(s) missing or wrong. Run: python scripts/download_models.py')
            return 1

    base_url = resolve_base_url(args.base_url)
    if not base_url:
        print('Cannot tell where to download from: GITHUB_REPO is empty in scripts/download_models.py and this folder has no\n'
              'GitHub remote. Set GITHUB_REPO, or pass --base-url, or set DEEPFAKE_MODELS_URL.')
        return 1

    failed = [n for n in todo if not fetch_one(n, base_url, models_dir)]
    if failed:
        print(f'{len(failed)} file(s) failed: {", ".join(failed)}. You can also download them by hand from the release page\n'
              f'and place them in {models_dir}, then run: python scripts/download_models.py --check')
        return 1
    print('All model weights downloaded and verified.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
