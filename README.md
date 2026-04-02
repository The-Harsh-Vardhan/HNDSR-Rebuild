# HNDSR Rebuild

HNDSR Rebuild is the standalone showcase repository for the current HNDSR research track. It keeps the latest script-first code, versioned Kaggle notebooks, review docs, and benchmark log without the legacy monorepo baggage.

## Current Story

- Active notebook cycle: `vR.1`
- Active model lane: scratch `SR3` baseline
- Active execution lane: Kaggle `4x-satellite-image-super-resolution`
- Paper-first adapter lane: `UCMerced`, `AID`, `RSSCN7`
- Current public status: notebook contract and Kaggle tooling are verified locally; the first standalone Kaggle training run is the next gate

## Research Protocol

This repo uses a constrained research loop:

- `program.md` defines the research process, keep/discard rules, and version-promotion gate
- `benchmarks/kaggle_runs.tsv` logs the public run history
- `scripts/validate_notebook_version.py` is the local gate before any Kaggle handoff
- `reports/reviews/` stores the review and roast for each immutable notebook version

The key idea is simple: keep the benchmark contract stable inside a version, patch only what is necessary, and fork a new version only when the experiment contract actually changes.

## Repo Layout

- `configs/`: experiment configs and phase defaults
- `src/`: dataset, metrics, tracker, contract, versioning, and model code
- `scripts/`: train, evaluate, sample export, Kaggle workflow, and version scaffolding
- `notebooks/`: control notebook and immutable Kaggle notebook versions
- `docs/`: workflow docs and paired notebook docs
- `reports/`: kickoff notes, smoke summaries, and review docs
- `benchmarks/`: tracked Kaggle experiment log
- `tests/`: contract and smoke checks

## Local Setup

1. Create a Python environment.
2. Install `requirements.txt`.
3. Populate the dataset roots expected in `configs/base.yaml` or edit them for your machine.
4. Run the contract checks:

```powershell
python -m pytest tests/test_kaggle_contract.py tests/test_notebook_contract.py tests/test_smoke_contract.py -q
python scripts/validate_notebook_version.py --version vR.1 --notebook notebooks/versions/vR.1_HNDSR.ipynb --doc docs/notebooks/vR.1_HNDSR.md --review reports/reviews/vR.1_HNDSR.review.md --config configs/phase1_sr3_vr1_kaggle.yaml --smoke-config configs/phase1_sr3_vr1_smoke.yaml --control-config configs/phase0_bicubic_vr1_kaggle_control.yaml
```

## Kaggle Loop

Run the current cycle from the repo root:

```powershell
python scripts/kaggle_workflow.py preflight vR.1
python scripts/upload_repo_to_kaggle.py
python scripts/kaggle_workflow.py run vR.1
python scripts/kaggle_workflow.py pull vR.1
```

Then:

1. sync the executed notebook and returned metrics
2. update `benchmarks/kaggle_runs.tsv`
3. write findings into `reports/reviews/vR.1_HNDSR.review.md`
4. decide whether to keep, patch, or promote

## Versioning Rules

- Scratch lineage: `vR.x_HNDSR.ipynb`
- External pretrained lineage: `vR.P.x_HNDSR.ipynb`
- Every notebook version must have:
  - `docs/notebooks/<stem>.md`
  - `reports/reviews/<stem>.review.md`
- Scaffold the next version only after review:

```powershell
python scripts/scaffold_version.py --from-version vR.1 --to-version vR.2 --activate-kaggle
```

## Dataset Policy

- Paper-first lane: `UCMerced`, `AID`, `RSSCN7`
- Control lane: Kaggle `4x-satellite-image-super-resolution`
- HR-only paper datasets use deterministic synthetic `4x` LR generation
- Kaggle remains paired LR/HR

## License

This repo is released under the MIT License in `LICENSE`.
