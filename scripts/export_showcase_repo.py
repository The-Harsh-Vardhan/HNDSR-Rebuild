#!/usr/bin/env python3
"""Export the rebuild track as a standalone showcase repository."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


TRACK_ROOT = Path(__file__).resolve().parents[1]
MONOREPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DEST = MONOREPO_ROOT / "showcase_repos" / "HNDSR-Rebuild"
COPY_ENTRIES = (
    "configs",
    "docs",
    "kaggle",
    "notebooks",
    "reports",
    "scripts",
    "src",
    "tests",
)
TEXT_SUFFIXES = {".py", ".md", ".yaml", ".yml", ".json", ".ipynb", ".txt"}
PATH_REWRITES = (
    ("", ""),
    ("", ""),
)

README_TEMPLATE = """# HNDSR Rebuild

HNDSR Rebuild is the clean standalone research repository for the latest HNDSR track. It keeps the current code, versioned notebooks, workflow docs, and review reports without the legacy monorepo baggage.

## What This Repo Shows

- The current script-first research workflow under `src/`, `scripts/`, and `configs/`
- Immutable Kaggle notebook versions under `notebooks/versions/`
- Notebook documentation under `docs/notebooks/`
- Review and audit records under `reports/reviews/`
- The paper-first dataset adapter lane plus the Kaggle 4x control lane

## Layout

- `configs/`: experiment configs and phase defaults
- `src/`: dataset, metrics, tracker, contract, and model code
- `scripts/`: train, evaluate, export, ablation, Kaggle, and export helpers
- `notebooks/`: control notebook and versioned Kaggle notebooks
- `docs/`: workflow docs and paired notebook docs
- `reports/`: kickoff notes, bootstrap summaries, smoke results, and reviews
- `tests/`: contract and smoke checks

## Quick Start

1. Create a Python environment.
2. Install `requirements.txt`.
3. Populate the dataset roots expected in `configs/base.yaml` or edit them for your machine.
4. Run the baseline checks:

```powershell
python scripts/evaluate_run.py --config configs/phase0_bicubic_kaggle_control_smoke.yaml
python scripts/train_baseline.py --config configs/phase1_sr3_smoke.yaml --run-name sr3-smoke
python scripts/evaluate_run.py --config configs/phase1_sr3_smoke.yaml --run-name sr3-smoke-eval
python scripts/validate_notebook_version.py --version vR.1 --notebook notebooks/versions/vR.1_HNDSR.ipynb --doc docs/notebooks/vR.1_HNDSR.md --review reports/reviews/vR.1_HNDSR.review.md --config configs/phase1_sr3_vr1_kaggle.yaml --smoke-config configs/phase1_sr3_vr1_smoke.yaml --control-config configs/phase0_bicubic_vr1_kaggle_control.yaml
```

## Dataset Policy

- Paper-first lane: `UCMerced`, `AID`, `RSSCN7`
- Control lane: Kaggle `4x-satellite-image-super-resolution`
- HR-only paper datasets use deterministic synthetic `4x` LR generation
- Kaggle stays paired LR/HR

## Notebook Versioning

- Scratch lineage: `vR.x_HNDSR.ipynb`
- External pretrained lineage: `vR.P.x_HNDSR.ipynb`
- Every notebook must have:
  - `docs/notebooks/<stem>.md`
  - `reports/reviews/<stem>.review.md`

## Current Status

- `vR.1` is the first immutable scratch notebook for the SR3 baseline
- Kaggle workflow helpers are included
- The paper-dataset adapter path is implemented but not benchmark-ready until real local dataset roots are populated

## License

This repo is released under the MIT License in `LICENSE`.
"""

GITIGNORE_TEMPLATE = """# Python
__pycache__/
*.py[cod]
.pytest_cache/

# Environments
.venv/
venv/
env/

# Artifacts and temp files
artifacts/
.tmp/
wandb/
runs/
logs/

# Data
data/*
!data/README.md

# Jupyter
.ipynb_checkpoints/

# Kaggle and credentials
kaggle.json
.kaggle/
kaggle_staging/
hndsr-repo.zip

# OS/editor
.DS_Store
Thumbs.db
.vscode/
.idea/
"""

REQUIREMENTS_TEMPLATE = """numpy
Pillow
PyYAML
pytest
scikit-image
torch
torchvision
tqdm
wandb
lpips
"""

DATA_README_TEMPLATE = """# Data Layout

Populate local datasets under this directory or update `configs/base.yaml` to point somewhere else.

Expected defaults:

- `data/kaggle_4x/HR_0.5m`
- `data/kaggle_4x/LR_2m`
- `data/UCMerced/Images`
- `data/AID`
- `data/RSSCN7`

These folders are ignored by Git.
"""

PYTEST_INI_TEMPLATE = """[pytest]
cache_dir = .tmp/pytest-cache
"""

BASE_CONFIG_TEMPLATE = """seed: 42

project:
  name: hndsr-research-track
  group: bootstrap
  tags:
    - smoke

paths:
  artifact_root: "artifacts"
  report_root: "reports"
  datasets:
    kaggle_4x:
      hr_dir: "data/kaggle_4x/HR_0.5m"
      lr_dir: "data/kaggle_4x/LR_2m"
    ucmerced:
      root_dir: "data/UCMerced/Images"
    aid:
      root_dir: "data/AID"
    rsscn7:
      root_dir: "data/RSSCN7"

dataset:
  family: kaggle
  name: kaggle_4x
  pairing_mode: paired
  scale_factor: 4

data:
  patch_size: 64
  batch_size: 2
  num_workers: 0
  val_split: 0.1
  fixed_scale: 4
  train_limit: null
  val_limit: 8

tracking:
  enabled: true
  mode: "offline"
  project: "hndsr-research-track"
  entity: null
  notes: "Isolated HNDSR rebuild track"

model:
  kind: bicubic
  model_channels: 32

training:
  epochs: 1
  lr: 1.0e-4
  weight_decay: 1.0e-4
  grad_clip: 1.0
  max_train_batches: 4
  max_val_batches: 2
  checkpoint_name: "baseline.pt"

diffusion:
  num_timesteps: 1000
  beta_start: 1.0e-4
  beta_end: 0.02
  inference_steps: 20

evaluation:
  split: "val"
  sample_limit: 8
  save_limit: 8
  compute_lpips: true
  grid_name: "comparison_grid.png"
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export a standalone showcase repo")
    parser.add_argument(
        "--dest",
        default=str(DEFAULT_DEST),
        help=f"Destination directory (default: {DEFAULT_DEST})",
    )
    return parser.parse_args()


def copy_entry(name: str, dest_root: Path) -> None:
    source = TRACK_ROOT / name
    target = dest_root / name
    if source.is_dir():
        shutil.copytree(source, target)
    else:
        shutil.copy2(source, target)


def rewrite_text_file(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    for old, new in PATH_REWRITES:
        text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")


def rewrite_tree(dest_root: Path) -> None:
    for path in dest_root.rglob("*"):
        if path.is_file() and path.suffix in TEXT_SUFFIXES:
            rewrite_text_file(path)


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_root_files(dest_root: Path) -> None:
    shutil.copy2(MONOREPO_ROOT / "LICENSE", dest_root / "LICENSE")
    write_file(dest_root / "README.md", README_TEMPLATE)
    write_file(dest_root / ".gitignore", GITIGNORE_TEMPLATE)
    write_file(dest_root / "requirements.txt", REQUIREMENTS_TEMPLATE)
    write_file(dest_root / "pytest.ini", PYTEST_INI_TEMPLATE)
    write_file(dest_root / "data" / "README.md", DATA_README_TEMPLATE)
    write_file(dest_root / "configs" / "base.yaml", BASE_CONFIG_TEMPLATE)


def ensure_safe_destination(dest_root: Path) -> None:
    resolved = dest_root.resolve()
    allowed_root = (MONOREPO_ROOT / "showcase_repos").resolve()
    if allowed_root not in resolved.parents:
        raise ValueError(f"Destination must stay under {allowed_root}")
    if dest_root.exists():
        raise FileExistsError(f"Destination already exists: {dest_root}")


def main() -> None:
    args = parse_args()
    dest_root = Path(args.dest)
    ensure_safe_destination(dest_root)
    dest_root.parent.mkdir(parents=True, exist_ok=True)
    for entry in COPY_ENTRIES:
        copy_entry(entry, dest_root)
    write_root_files(dest_root)
    rewrite_tree(dest_root)
    print(f"Standalone showcase repo exported to {dest_root}")


if __name__ == "__main__":
    main()
