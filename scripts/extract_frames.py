import cv2
import os
from facenet_pytorch import MTCNN
from PIL import Image
import torch
from tqdm import tqdm

device = 'cpu'
print(f'Using device: {device}')
mtcnn = MTCNN(image_size=224, margin=20, device=device)

def extract_faces(video_path, output_dir, max_frames=30):
    os.makedirs(output_dir, exist_ok=True)
    cap = cv2.VideoCapture(video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    sample_interval = max(1, fps)
    saved = 0
    frame_idx = 0

    while cap.isOpened() and saved < max_frames:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % sample_interval == 0:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)
            face = mtcnn(img)
            if face is not None:
                face_img = (face.permute(1,2,0).numpy() * 128 + 127.5).clip(0,255).astype('uint8')
                out_path = os.path.join(output_dir, f'frame_{frame_idx:05d}.jpg')
                Image.fromarray(face_img).save(out_path)
                saved += 1
        frame_idx += 1

    cap.release()
    return saved

def process_dataset(video_dir, output_dir, label, only=None):
    videos = [f for f in os.listdir(video_dir) if f.endswith('.mp4')]
    if only is not None:
        videos = [f for f in videos if os.path.splitext(f)[0] in only]
    print(f'\nProcessing {len(videos)} {label} videos...')
    total_faces = 0
    for video in tqdm(videos):
        video_path = os.path.join(video_dir, video)
        video_name = os.path.splitext(video)[0]
        out_dir = os.path.join(output_dir, video_name)
        faces = extract_faces(video_path, out_dir)
        total_faces += faces
    print(f'Done. {total_faces} face crops saved to {output_dir}')

if __name__ == '__main__':
    import argparse
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    ap = argparse.ArgumentParser(description='Extract MTCNN face crops from FF++ c23 videos.')
    ap.add_argument('--fake-method', default='Deepfakes',
                    help='FF++ manipulation method folder under data/manipulated_sequences/.')
    ap.add_argument('--fake-only', action='store_true',
                    help='Skip the real videos (used for extra manipulation methods).')
    ap.add_argument('--out-root', default=str(root / 'frames'),
                    help='Default reproduces the training layout: <out>/real/<id>/ and <out>/fake/<pair>/. '
                         'With --fake-only, fakes go straight to <out>/<pair>/ (use a separate folder per '
                         'method, e.g. frames_methods/FaceSwap, so pair names never collide with frames/fake).')
    ap.add_argument('--only-split', choices=['train', 'val', 'test'], default=None,
                    help='Extract only fake videos assigned to this split in the frozen manifest '
                         '(data_splits/split_v2_identity_grouped.json). Use "test" for the zero-shot '
                         'cross-method evaluation.')
    args = ap.parse_args()

    only = None
    if args.only_split:
        import json
        assign = json.load(open(root / 'data_splits' / 'split_v2_identity_grouped.json'))['assignment']
        only = {k.split('/', 1)[1] for k, v in assign.items() if k.startswith('fake/') and v == args.only_split}

    out = Path(args.out_root)
    if not args.fake_only:
        process_dataset(str(root / 'data/original_sequences/youtube/c23/videos'), str(out / 'real'), 'real')
    fake_out = out if args.fake_only else out / 'fake'
    process_dataset(str(root / 'data/manipulated_sequences' / args.fake_method / 'c23/videos'),
                    str(fake_out), f'fake ({args.fake_method})', only=only)
