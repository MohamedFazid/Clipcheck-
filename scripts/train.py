"""Train the video branch (seeded, optionally regularised).

Architecture is chosen with --arch (default efficientnet_b4, the PPR incumbent); any timm image classifier works.

TWO CHANGES vs the version that produced the Draft Project Report's baseline
figures, both of them deliberate and both flagged in that report as planned
work:

1. AUGMENTATION TRANSFORM BUG FIXED (Ch4.3 / Ch5.6 improvement #2).
   The old code built train/val/test as three Subsets over ONE shared
   ImageFolder. Because `transform` is a property of the shared dataset, the
   last assignment won and the validation (no-augmentation) transform was
   applied to all three splits -- so RandomHorizontalFlip / ColorJitter never
   actually ran during training. This version builds a SEPARATE ImageFolder
   per transform and indexes both with the SAME split indices, so the splits
   are byte-for-byte the same samples as the baseline while the training
   split now genuinely gets augmented.

   Because random_split's permutation depends only on the total length and the
   generator seed (not on dataset contents), splitting range(n) here yields
   exactly the indices the baseline used. The test set is therefore identical
   and results remain directly comparable.

   Pass --no-augment to reproduce the old (unaugmented) training condition
   with this clean code path -- useful for isolating the augmentation effect
   from the regularisation effect.

2. REGULARISATION IS AVAILABLE BUT OPT-IN (Ch3.7 Phase 2).
   --dropout, --label-smoothing and --early-stopping-patience all default to
   OFF, so the default command reproduces the baseline training recipe. The
   regularised condition the report specifies is:
       --dropout 0.3 --label-smoothing 0.1 --early-stopping-patience 3

Checkpoint selection: with early stopping enabled the checkpoint is taken at
the best validation LOSS (the same quantity the stopping criterion watches);
without it, the baseline's best-validation-ACCURACY rule is kept. This is a
deliberate pairing, not an oversight -- mixing a loss-based stop with an
accuracy-based checkpoint would stop on one signal and select on another.

Use --tag to write into an isolated results/models subdirectory so a new
experiment never overwrites the reported baseline artifacts.

Examples:
    python scripts/train.py --seed 42
    python scripts/train.py --seed 42 --tag reg --dropout 0.3 \
        --label-smoothing 0.1 --early-stopping-patience 3
"""

import os
import sys
from pathlib import Path
import json
import argparse

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Subset
from torchvision import datasets, transforms
import timm
from tqdm import tqdm

# Allow running as `python scripts/train.py` from the project root.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import (
    FRAMES_DIR, MODEL_RUNS_DIR, RUNS_DIR, SPLIT_SEED, PROJECT_ROOT,
    run_paths, set_seed, get_device, get_split,
)

# ── Args ─────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description='Train the video branch (seeded); --arch selects the architecture.')
parser.add_argument('--seed', type=int, default=42,
                    help='Training seed (controls head init, shuffle, augmentation). '
                         'The data split is held fixed at SPLIT_SEED regardless.')
parser.add_argument('--tag', type=str, default='',
                    help='Optional experiment tag. Isolates checkpoints/results in a '
                         'subdirectory so the reported baseline is never overwritten.')
parser.add_argument('--arch', type=str, default='efficientnet_b4',
                    help='timm model name (ImageNet-pretrained). Default is the PPR incumbent; '
                         'the model bake-off varies this with an otherwise identical recipe.')
parser.add_argument('--frames-dir', type=str, default=None,
                    help='Folder of <class>/<video>/frame_*.jpg. Default: frames/. Non-default folders '
                         '(e.g. frames_multi/) take their split from the frozen manifest.')
parser.add_argument('--fold', type=int, default=None,
                    help='Cross-validation fold 0-4 from data_splits/cv5_identity_grouped.json (train 70 / val 10 / test 20 '
                         'identity groups). Default: the main frozen split.')
parser.add_argument('--epochs', type=int, default=10, help='Max training epochs.')
parser.add_argument('--dropout', type=float, default=0.0,
                    help='Dropout before the classifier head (report specifies 0.3 '
                         'for the regularised condition). 0.0 = baseline.')
parser.add_argument('--label-smoothing', type=float, default=0.0,
                    help='Label smoothing for cross-entropy (report specifies 0.1). '
                         '0.0 = baseline.')
parser.add_argument('--early-stopping-patience', type=int, default=0,
                    help='Stop after this many epochs with no validation-loss '
                         'improvement. 0 disables early stopping (baseline).')
parser.add_argument('--no-augment', action='store_true',
                    help='Disable train-time augmentation, reproducing the '
                         'pre-bug-fix training condition on the clean code path.')
args = parser.parse_args()

# Seed everything BEFORE model creation / dataloader construction so that
# classifier-head init and shuffle order are reproducible for this seed.
set_seed(args.seed)

device = get_device()
print(f'Using device: {device} | training seed: {args.seed} | split seed: {SPLIT_SEED}')

DATA_DIR = str(Path(args.frames_dir).resolve()) if args.frames_dir else str(FRAMES_DIR)
model_path, run_dir = run_paths(args.seed, args.tag)
os.makedirs(model_path.parent, exist_ok=True)
os.makedirs(run_dir, exist_ok=True)

BATCH_SIZE = 32
EPOCHS = args.epochs
LR = 1e-4
IMG_SIZE = 224

augment = not args.no_augment
print(f'Augmentation: {"ON" if augment else "OFF"} | dropout: {args.dropout} | '
      f'label smoothing: {args.label_smoothing} | '
      f'early stopping patience: {args.early_stopping_patience or "disabled"}')
print(f'Checkpoint -> {model_path}')
print(f'Run dir    -> {run_dir}')

val_transforms = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406],
                         [0.229, 0.224, 0.225]),
])

if augment:
    train_transforms = transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.RandomHorizontalFlip(),
        transforms.ColorJitter(brightness=0.2, contrast=0.2),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406],
                             [0.229, 0.224, 0.225]),
    ])
else:
    train_transforms = val_transforms

# ── Splits: two datasets, one set of indices (the transform-bug fix) ─────────
# Separate ImageFolder instances mean each split carries its OWN transform,
# instead of three Subsets sharing one mutable dataset object.
train_source = datasets.ImageFolder(DATA_DIR, transform=train_transforms)
eval_source = datasets.ImageFolder(DATA_DIR, transform=val_transforms)

print(f'Classes: {train_source.classes}')
print(f'Total samples: {len(train_source)}')

# Identity-disjoint split (see utils.grouped_video_split docstring): every
# frame of a given video, AND every video built from a given real identity
# (through FF++'s reciprocal Deepfakes pairing), is assigned to exactly one
# of train/val/test. Fixes a confirmed leak in the previous frame-level
# random_split, where 100% of test-set videos also had frames in train.
train_idx, val_idx, test_idx = get_split(train_source, args.frames_dir, split_seed=SPLIT_SEED, fold=args.fold)

train_set = Subset(train_source, list(train_idx))   # augmented (if enabled)
val_set = Subset(eval_source, list(val_idx))        # never augmented
test_set = Subset(eval_source, list(test_idx))      # never augmented

# Explicit generator makes the shuffle order reproducible per training seed.
loader_gen = torch.Generator().manual_seed(args.seed)
train_loader = DataLoader(train_set, batch_size=BATCH_SIZE, shuffle=True,
                          num_workers=0, generator=loader_gen)
val_loader = DataLoader(val_set, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

print(f'Train: {len(train_set)} | Val: {len(val_set)} | Test: {len(test_set)}')

model = timm.create_model(args.arch, pretrained=True, num_classes=2,
                          drop_rate=args.dropout)
model = model.to(device)
print(f'{args.arch} loaded with pretrained ImageNet weights '
      f'(drop_rate={args.dropout})')

criterion = nn.CrossEntropyLoss(label_smoothing=args.label_smoothing)
optimizer = torch.optim.Adam(model.parameters(), lr=LR)
scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=3, gamma=0.5)

early_stopping = args.early_stopping_patience > 0
best_val_acc = 0.0
best_val_loss = float('inf')
epochs_without_improvement = 0
stopped_early_at = None
history = {'train_loss': [], 'train_acc': [], 'val_loss': [], 'val_acc': []}

for epoch in range(EPOCHS):
    model.train()
    train_loss, train_correct, train_total = 0, 0, 0

    for images, labels in tqdm(train_loader, desc=f'Epoch {epoch+1}/{EPOCHS} [Train]'):
        images, labels = images.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        train_loss += loss.item()
        preds = outputs.argmax(dim=1)
        train_correct += (preds == labels).sum().item()
        train_total += labels.size(0)

    train_acc = train_correct / train_total
    train_loss /= len(train_loader)

    model.eval()
    val_loss, val_correct, val_total = 0, 0, 0
    with torch.no_grad():
        for images, labels in val_loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            loss = criterion(outputs, labels)
            val_loss += loss.item()
            preds = outputs.argmax(dim=1)
            val_correct += (preds == labels).sum().item()
            val_total += labels.size(0)

    val_acc = val_correct / val_total
    val_loss /= len(val_loader)
    scheduler.step()

    history['train_loss'].append(train_loss)
    history['train_acc'].append(train_acc)
    history['val_loss'].append(val_loss)
    history['val_acc'].append(val_acc)

    print(f'Epoch {epoch+1}: train_loss={train_loss:.4f} train_acc={train_acc:.4f} '
          f'val_loss={val_loss:.4f} val_acc={val_acc:.4f}')

    # ── Checkpoint + early stopping ──────────────────────────────────────────
    if early_stopping:
        # Stop and select on the SAME signal: validation loss.
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_val_acc = max(best_val_acc, val_acc)
            epochs_without_improvement = 0
            torch.save(model.state_dict(), model_path)
            print(f'  -> Best model saved (val_loss={val_loss:.4f}) -> {model_path}')
        else:
            epochs_without_improvement += 1
            print(f'  -> No val_loss improvement '
                  f'({epochs_without_improvement}/{args.early_stopping_patience})')
            if epochs_without_improvement >= args.early_stopping_patience:
                stopped_early_at = epoch + 1
                print(f'  -> Early stopping at epoch {stopped_early_at} '
                      f'(best val_loss={best_val_loss:.4f})')
                break
    else:
        # Baseline rule: keep the best-validation-accuracy checkpoint.
        best_val_loss = min(best_val_loss, val_loss)
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), model_path)
            print(f'  -> Best model saved (val_acc={val_acc:.4f}) -> {model_path}')

config = {
    'arch': args.arch,
    'frames_dir': os.path.relpath(DATA_DIR, PROJECT_ROOT),
    'fold': args.fold,
    'seed': args.seed,
    'tag': args.tag,
    'epochs_requested': EPOCHS,
    'epochs_run': len(history['train_loss']),
    'stopped_early_at': stopped_early_at,
    'augmentation': augment,
    'dropout': args.dropout,
    'label_smoothing': args.label_smoothing,
    'early_stopping_patience': args.early_stopping_patience,
    'checkpoint_criterion': 'val_loss' if early_stopping else 'val_acc',
    'best_val_acc': best_val_acc,
    'best_val_loss': best_val_loss,
    'split_seed': SPLIT_SEED,
    'batch_size': BATCH_SIZE,
    'lr': LR,
}

with open(run_dir / 'history.json', 'w') as f:
    json.dump(history, f, indent=2)
with open(run_dir / 'train_config.json', 'w') as f:
    json.dump(config, f, indent=2)

print(f'\nTraining complete (seed {args.seed}, tag {args.tag or "baseline"}).')
print(f'Best val accuracy: {best_val_acc:.4f} | best val loss: {best_val_loss:.4f}')
print(f'Model saved to {model_path}')
