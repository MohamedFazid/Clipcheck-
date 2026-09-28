"""Pure video-branch inference (no UI dependency).

Shared by the web app (server.py) and the integration tests: load the model +
MTCNN, run a video through frame-sampling -> face crop -> the shipped image
classifier, and return the aggregated P(video_fake) verdict. The classifier
architecture is read from models/shipped_model.json (see scripts/ship_model.py);
without that file it is EfficientNet-B4, the original default.
"""

import json
import os
import sys

import numpy as np
import torch
import cv2
from PIL import Image
from facenet_pytorch import MTCNN
import timm
from torchvision import transforms

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import MODELS_DIR, get_device

IMG_SIZE = 224
CLASS_NAMES = ['fake', 'real']          # ImageFolder order: index 0 = fake

_val_transforms = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])


# Training crops were saved as JPEG by scripts/extract_frames.py with PIL's default quality (75), so the model was
# trained and evaluated on JPEG-compressed crops. Feeding it uncompressed in-memory crops shifts its operating point
# (measured: two real test videos flip to fake and 7 of 88 verdicts change; see results/preprocessing_parity/), so
# inference applies the same round trip. Ranking quality (AUC) is unaffected either way.
TRAINING_JPEG_QUALITY = 75


def training_style(face_pil, quality=TRAINING_JPEG_QUALITY):
    """JPEG round trip that reproduces how the training crops were stored."""
    import io
    buf = io.BytesIO()
    face_pil.save(buf, format='JPEG', quality=quality)
    return Image.open(io.BytesIO(buf.getvalue())).convert('RGB')


def shipped_arch(default='efficientnet_b4'):
    """timm architecture of the model promoted to models/best_model.pth."""
    p = MODELS_DIR / 'shipped_model.json'
    if p.exists():
        try:
            return json.load(open(p)).get('arch') or default
        except (OSError, json.JSONDecodeError):
            pass
    return default


def shipped_temperature(default=1.0):
    """Calibration temperature of the shipped model (models/shipped_model.json, key 'temperature'); 1.0 = none."""
    p = MODELS_DIR / 'shipped_model.json'
    if p.exists():
        try:
            return float(json.load(open(p)).get('temperature', default))
        except (OSError, ValueError, json.JSONDecodeError):
            pass
    return default


# timm architecture name -> the name shown to users. Every place that names the video model (sidebar, "models that ran"
# table, face-crop caption, latency labels) goes through video_model_summary(), so shipping a different architecture
# cannot leave a stale name behind (the Draft Report, 4.6 and 5.5, is explicit that an app must not misstate its status).
ARCH_DISPLAY_NAMES = {
    'efficientnet_b4': 'EfficientNet-B4', 'efficientnet_b0': 'EfficientNet-B0', 'resnet50': 'ResNet-50',
    'legacy_xception': 'Xception', 'convnext_tiny': 'ConvNeXt-Tiny',
}


def arch_display_name(arch):
    return ARCH_DISPLAY_NAMES.get(arch, arch)


def video_model_summary(manifest_path=None):
    """What the app is actually serving as its video model, read from models/shipped_model.json.

    Returns a dict with: shipped (bool), arch, name (display name), tag, seed, trained_on, checkpoint (short sha256),
    accuracy_source and status (a one-line, honest description). With no shipped_model.json the checkpoint is a legacy
    file that was never promoted through scripts/ship_model.py, so it is labelled as such rather than given a clean name."""
    p = manifest_path or (MODELS_DIR / 'shipped_model.json')
    m = None
    if os.path.exists(p):
        try:
            m = json.load(open(p))
        except (OSError, json.JSONDecodeError):
            m = None
    if m is None:
        arch = 'efficientnet_b4'
        return {'shipped': False, 'arch': arch, 'name': arch_display_name(arch), 'tag': None, 'seed': None,
                'trained_on': None, 'checkpoint': None, 'accuracy_source': None,
                'status': 'legacy checkpoint, not promoted through ship_model.py (trained on the superseded leaking split)'}
    arch = m.get('arch') or 'efficientnet_b4'
    trained_on = m.get('trained_on') or 'unrecorded'
    ck = (m.get('checkpoint_sha256') or '')[:12] or None
    return {'shipped': True, 'arch': arch, 'name': arch_display_name(arch), 'tag': m.get('tag'), 'seed': m.get('seed'),
            'trained_on': trained_on, 'checkpoint': ck, 'accuracy_source': m.get('video_accuracy_source'),
            'status': f'fine-tuned on FaceForensics++ c23, {trained_on}' + (f'; checkpoint {ck}' if ck else '')}


SHIPPED_CHECKPOINT = MODELS_DIR / 'best_model.pth'


def is_shipped_checkpoint(model_path):
    """True when model_path is the shipped checkpoint (or None, which means it). Callers that pass the path explicitly
    (server.py, eval_fallback_4condition.py) must get the SHIPPED architecture, not the historical default: before this
    check existed, shipping a non-EfficientNet-B4 model made both of them fail to load it (RuntimeError: size mismatch)."""
    if model_path is None:
        return True
    try:
        return os.path.realpath(str(model_path)) == os.path.realpath(str(SHIPPED_CHECKPOINT))
    except OSError:
        return False


def load_models(model_path=None, arch=None):
    """Load MTCNN and the classifier.

    The architecture comes from models/shipped_model.json whenever the checkpoint being loaded IS the shipped one, whether
    model_path is None or the shipped path spelled out. For any other checkpoint pass arch= explicitly; it falls back to
    EfficientNet-B4 (the historical default) only to keep old single-checkpoint call sites working."""
    device = get_device()
    mtcnn = MTCNN(image_size=IMG_SIZE, margin=20, device='cpu',
                  keep_all=False, select_largest=True)
    shipped = is_shipped_checkpoint(model_path)
    arch = arch or (shipped_arch() if shipped else 'efficientnet_b4')
    model = timm.create_model(arch, pretrained=False, num_classes=2)
    model.load_state_dict(torch.load(model_path or str(MODELS_DIR / 'best_model.pth'),
                                     map_location=device))
    model = model.to(device).eval()
    # Logits are divided by this before the softmax (1.0 = uncalibrated). Only the shipped model can carry one.
    model.calibration_temperature = shipped_temperature() if shipped else 1.0
    return mtcnn, model, device


def sample_face_crops(video_path, mtcnn, max_faces=20, on_progress=None):
    """The app's exact frame-sampling and face-cropping path: about 3 frames per second, MTCNN, up to max_faces
    crops, returned as in-memory PIL images (no JPEG round trip). Empty list if the video cannot be opened or no
    face is found. Shared by analyse_video_file and scripts/check_preprocessing_parity.py so the parity check
    tests the real path, not a copy of it."""
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return []
    fps = int(cap.get(cv2.CAP_PROP_FPS)) or 25
    interval = max(1, fps // 3)

    crops = []
    frame_idx = 0
    while cap.isOpened() and len(crops) < max_faces:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % interval == 0:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_tensor = mtcnn(Image.fromarray(rgb))
            if face_tensor is not None:
                crops.append(Image.fromarray(
                    ((face_tensor.permute(1, 2, 0).numpy() * 128) + 127.5)
                    .clip(0, 255).astype('uint8')))
                if on_progress is not None:
                    on_progress(min(len(crops) / max_faces, 1.0), f'Analysed {len(crops)} face crop(s)…')
        frame_idx += 1
    cap.release()
    return crops


def analyse_video_file(video_path, mtcnn, model, device, max_faces=20, on_progress=None, match_training_jpeg=True,
                       return_features=False):
    """Return dict(p_fake, per_frame, n_faces, verdict, sample_face) or None if no faces found.

    sample_face is a PIL image of the first successfully detected face crop (for UI preview); on_progress(fraction,
    text) is an optional callback for UI progress bars. match_training_jpeg=True (default) applies the JPEG round trip the
    training crops went through (see TRAINING_JPEG_QUALITY); False feeds raw in-memory crops. This is the single video-branch inference path, used by the
    web app (server.py), the evaluation scripts and tests/test_pipeline.py.
    """
    crops = sample_face_crops(video_path, mtcnn, max_faces, on_progress)
    if not crops:
        return None
    if on_progress is not None:     # UI only: tells the progress screen that face finding is done and scoring has started
        on_progress(1.0, f'Scoring {len(crops)} face crop(s)…')
    temperature = getattr(model, 'calibration_temperature', 1.0)
    fake_probs, features = [], []
    for face_pil in crops:
        model_input = training_style(face_pil) if match_training_jpeg else face_pil
        tensor = _val_transforms(model_input).unsqueeze(0).to(device)
        with torch.no_grad():
            if return_features:
                # Same forward pass split in two (forward_head(forward_features(x)) == model(x), checked in
                # tests/test_ood_gate.py), so the pooled features the out-of-domain gate reads cost no second pass.
                fmap = model.forward_features(tensor)
                logits = model.forward_head(fmap)
                features.append(model.forward_head(fmap, pre_logits=True)[0].float().cpu().numpy())
            else:
                logits = model(tensor)
            fake_probs.append(torch.softmax(logits / temperature, dim=1)[0, 0].item())
    p_fake = float(np.mean(fake_probs))
    out = {
        'p_fake': p_fake,
        'per_frame': fake_probs,
        'n_faces': len(fake_probs),
        'verdict': 'FAKE' if p_fake >= 0.5 else 'REAL',
        'sample_face': crops[0],
    }
    if return_features:
        out['features'] = np.stack(features)
    return out
