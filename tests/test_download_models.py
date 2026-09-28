"""Tests for scripts/download_models.py: its checksums match the model card, a good download is verified and moved into
place, a corrupted one is discarded, and the GitHub release URL is built correctly. Data-free: the downloads are served
from a temporary folder by a local HTTP server, never the internet."""
import functools
import hashlib
import http.server
import re
import sys
import threading
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))
import download_models as dm  # noqa: E402


def test_checksums_match_model_card():
    card = (PROJECT_ROOT / 'models' / 'README.md').read_text()
    for name, (sha, _) in dm.MODEL_FILES.items():
        row = re.search(rf'^\| `{re.escape(name)}` .*`([0-9a-f]{{64}})` \|$', card, re.M)
        assert row, f'{name} has no row in models/README.md'
        assert row.group(1) == sha, f'{name}: checksum differs between download_models.py and models/README.md'


def test_weights_are_git_ignored():
    ignore = (PROJECT_ROOT / '.gitignore').read_text()
    assert 'models/*.pth' in ignore and 'models/*.joblib' in ignore and 'models/*.part' in ignore


@pytest.mark.parametrize('url,expected', [
    ('https://github.com/alice/multimodal-deepfake-detector.git', 'alice/multimodal-deepfake-detector'),
    ('git@github.com:alice/multimodal-deepfake-detector.git', 'alice/multimodal-deepfake-detector'),
    ('https://github.com/alice/repo', 'alice/repo'),
])
def test_repo_parsed_from_remote(monkeypatch, url, expected):
    class Done:
        stdout = url + '\n'
    monkeypatch.setattr(dm.subprocess, 'run', lambda *a, **k: Done())
    assert dm.repo_from_git_remote() == expected


def test_base_url_precedence(monkeypatch):
    monkeypatch.setattr(dm, 'GITHUB_REPO', 'alice/repo')
    monkeypatch.delenv('DEEPFAKE_MODELS_URL', raising=False)
    assert dm.resolve_base_url() == f'https://github.com/alice/repo/releases/download/{dm.RELEASE_TAG}'
    monkeypatch.setenv('DEEPFAKE_MODELS_URL', 'http://mirror/models/')
    assert dm.resolve_base_url() == 'http://mirror/models'
    assert dm.resolve_base_url('http://cli/x') == 'http://cli/x'


@pytest.fixture
def served(tmp_path, monkeypatch):
    """A local HTTP server over tmp_path/'release'; MODEL_FILES is replaced with two small files it serves."""
    release = tmp_path / 'release'
    release.mkdir()
    files = {}
    for name, body in [('a.pth', b'weights-a' * 1000), ('b.joblib', b'weights-b' * 500)]:
        (release / name).write_bytes(body)
        files[name] = (hashlib.sha256(body).hexdigest(), len(body))
    monkeypatch.setattr(dm, 'MODEL_FILES', files)
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(release))
    handler.log_message = lambda *a: None
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    models = tmp_path / 'models'
    models.mkdir()
    yield release, models, f'http://127.0.0.1:{server.server_address[1]}'
    server.shutdown()


def test_download_verifies_and_is_idempotent(served):
    release, models, url = served
    assert dm.main(['--base-url', url, '--models-dir', str(models)]) == 0
    for name in dm.MODEL_FILES:
        assert (models / name).read_bytes() == (release / name).read_bytes()
    assert not list(models.glob('*.part'))
    assert dm.main(['--check', '--models-dir', str(models)]) == 0
    assert dm.main(['--base-url', 'http://127.0.0.1:1', '--models-dir', str(models)]) == 0   # nothing to fetch


def test_corrupted_download_is_discarded(served):
    release, models, url = served
    (release / 'a.pth').write_bytes(b'tampered')
    assert dm.main(['--base-url', url, '--models-dir', str(models)]) == 1
    assert not (models / 'a.pth').exists() and not (models / 'a.pth.part').exists()
    assert (models / 'b.joblib').exists()


def test_wrong_local_file_is_replaced(served):
    release, models, url = served
    (models / 'a.pth').write_bytes(b'stale')
    assert dm.main(['--check', '--models-dir', str(models)]) == 1
    assert dm.main(['--base-url', url, '--models-dir', str(models)]) == 0
    assert (models / 'a.pth').read_bytes() == (release / 'a.pth').read_bytes()


def test_missing_release_file_fails_cleanly(served):
    release, models, url = served
    (release / 'b.joblib').unlink()
    assert dm.main(['--base-url', url, '--models-dir', str(models)]) == 1
    assert not (models / 'b.joblib').exists()


def test_if_missing_downloads_only_absent_files(served):
    release, models, url = served
    (models / 'a.pth').write_bytes(b'present, not hashed in this mode')
    assert dm.main(['--if-missing', '--base-url', url, '--models-dir', str(models)]) == 0
    assert (models / 'a.pth').read_bytes() == b'present, not hashed in this mode'
    assert (models / 'b.joblib').exists()
