# HNDSR Rebuild

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
