# vR.1 HNDSR

## Objective

`vR.1 HNDSR` is the first immutable Kaggle notebook in the scratch lineage. Its job is not to chase peak metrics yet. Its job is to prove that the rebuild track can train, evaluate, export artifacts, and log stable metadata on Kaggle without notebook-only model logic.

## Scope

- Dataset lane: Kaggle `4x-satellite-image-super-resolution`
- Model lane: scratch `SR3` baseline from `src/models.py`
- Control lane: bicubic evaluation using the same Kaggle split and smoke pack
- Tracker mode: `offline` by default, upgrade to `online` only after W&B authentication is known-good

## Config Contract

- Full training config: `configs/phase1_sr3_vr1_kaggle.yaml`
- Smoke training config: `configs/phase1_sr3_vr1_smoke.yaml`
- Bicubic control config: `configs/phase0_bicubic_vr1_kaggle_control.yaml`
- Fixed scale: `4x`
- Run names used in notebook:
  - `vR.1-control`
  - `vR.1-smoke`
  - `vR.1-smoke-eval`
  - `vR.1-train`
  - `vR.1-eval`

## Kaggle Run Guide

1. Open `notebooks/versions/vR.1_HNDSR.ipynb`.
2. Attach both datasets declared in `notebooks/versions/kernel-metadata.json`:
   - `cristobaltudela/4x-satellite-image-super-resolution`
   - `harshv777/hndsr-mini-project-code`
3. Run `python scripts/kaggle_workflow.py preflight vR.1` locally before handing the notebook to Kaggle.
4. Run the runtime diagnostics cells first and confirm the notebook finds the repo under `/kaggle/input/hndsr-mini-project-code/Mini Project`, or extracts `/kaggle/input/hndsr-mini-project-code/Mini Project.zip` into `/kaggle/working/HNDSR-Rebuild`, before training.
5. Confirm CUDA visibility if a GPU runtime is enabled.
6. Leave the repo-root debug output in place for the first Kaggle pass; it is there to catch bad dataset mounts early.
7. Run the readiness validator cell before any training cell.
8. Run the bicubic control evaluation to confirm the dataset and metrics path.
9. Run the smoke training cell to confirm script, checkpoint, and evaluation wiring.
10. Run the full training and full evaluation cells only after the smoke path succeeds.
11. Export the executed notebook, the generated metrics JSON, the comparison grid, and the best checkpoint path back into the repo workflow for review.

## Expected Artifacts

- Control eval summary JSON under `artifacts/vR.1-control/`
- Smoke checkpoint and metrics under `artifacts/vR.1-smoke/`
- Full training checkpoint and metrics under `artifacts/vR.1-train/`
- Full evaluation summary and image strips under `artifacts/vR.1-eval/`
- W&B local tracker records under each run's `tracker/` directory

## Known Constraints

- `vR.1` stays on the Kaggle control lane even though the broader rebuild track is paper-first.
- W&B defaults to offline mode to keep the first Kaggle pass stable.
- The notebook now checks both Kaggle working-directory mounts and the attached code-dataset mount before asserting the repo layout.
- The attached Kaggle code dataset may arrive as `Mini Project.zip`; `vR.1` extracts that archive into `/kaggle/working/HNDSR-Rebuild` before continuing.
- This notebook is allowed to orchestrate scripts, inspect configs, and render outputs. It is not allowed to carry unique model-training logic.

## Handoff Back For Review

Return all of the following after the Kaggle run:

- The executed `vR.1_HNDSR.ipynb`
- Any Kaggle-side edits required for runtime stability
- The best checkpoint path used for evaluation
- The control, smoke, and full evaluation JSON summaries
- The comparison grid image path
- A short note about runtime duration, GPU type, and any failure modes hit during the run
