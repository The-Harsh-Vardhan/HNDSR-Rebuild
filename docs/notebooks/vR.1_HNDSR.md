# vR.1 HNDSR

## Objective

`vR.1 HNDSR` is the first immutable Kaggle notebook in the scratch lineage. Its job is not to chase peak metrics yet. Its job is to prove that the rebuild track can train, evaluate, export artifacts, and log stable metadata on Kaggle without notebook-only model logic.

Completed outcome:

- Kaggle/W&B contract: passed
- Assigned GPU in the canonical run: `Tesla T4`
- Model outcome: failed baseline
- Freeze decision: keep `vR.1` immutable and move `vR.2` to a supervised SR reset

## Scope

- Dataset lane: Kaggle `4x-satellite-image-super-resolution`
- Model lane: scratch `SR3` baseline from `src/models.py`
- Control lane: bicubic evaluation using the same Kaggle split and smoke pack
- Tracker mode: authenticated `W&B online` only; decline the run if the Kaggle secret is missing
- Execution path: `kaggle kernels push` for upload, Kaggle editor launch for the actual secret-backed run

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
4. Push the latest repo snapshot with `python scripts/upload_repo_to_kaggle.py`, then upload the notebook metadata with `python scripts/kaggle_workflow.py push vR.1`.
5. Launch the actual run with `python scripts/kaggle_workflow.py run-editor vR.1`. Do not rely on CLI-triggered execution when `WANDB_API_KEY` is required.
6. Run the runtime diagnostics cells first and confirm the notebook finds the repo under one of the mounted `/kaggle/input/*` datasets, or extracts a mounted `Mini Project.zip` archive into `/kaggle/working/HNDSR-Rebuild`, before training.
7. Re-run `python scripts/upload_repo_to_kaggle.py` after any same-version Kaggle runtime patch so the attached repo dataset matches the notebook shell.
8. Confirm CUDA visibility if a GPU runtime is enabled.
9. Leave the repo-root debug output in place for the first Kaggle pass; it is there to catch bad dataset mounts early.
10. Confirm the W&B setup cell prints that authenticated online tracking is enforced. If it does not, stop and fix Kaggle secrets before continuing.
11. Run the readiness validator cell before any training cell.
12. Run the bicubic control evaluation to confirm the dataset and metrics path.
13. Run the smoke training cell to confirm script, checkpoint, and evaluation wiring.
14. Run the full training and full evaluation cells only after the smoke path succeeds.
15. Export the executed notebook, the generated metrics JSON, the comparison grid, and the best checkpoint path back into the repo workflow for review.

## Expected Artifacts

- Control eval summary JSON under `artifacts/vR.1-control/`
- Smoke checkpoint and metrics under `artifacts/vR.1-smoke/`
- Full training checkpoint and metrics under `artifacts/vR.1-train/`
- Full evaluation summary and image strips under `artifacts/vR.1-eval/`
- Authenticated W&B run links plus local tracker records under each run's `tracker/` directory

## Known Constraints

- `vR.1` stays on the Kaggle control lane even though the broader rebuild track is paper-first.
- `vR.1` now rejects Kaggle execution unless the `WANDB_API_KEY` secret is available and online tracking is enforced before the first validator or training command.
- Kaggle CLI upload metadata does not currently expose notebook secrets, so the authoritative run launch must come from the Kaggle editor path after the secret is attached.
- The notebook now checks both Kaggle working-directory mounts and the attached code-dataset mount before asserting the repo layout.
- The attached Kaggle code dataset may arrive under nested private-dataset paths such as `/kaggle/input/datasets/<owner>/<slug>` and may contain `Mini Project.zip`; `vR.1` now recurses through the Kaggle input tree and copies any discovered repo from the read-only input mount into `/kaggle/working/HNDSR-Rebuild` before validation or training writes artifacts.
- The runtime scripts now auto-resolve the Kaggle image dataset even when Kaggle wraps the image folders inside duplicated directories such as `/kaggle/input/4x-satellite-image-super-resolution/HR_0.5m/HR_0.5m` and `/LR_2m/LR_2m`.
- Kaggle metadata can request `GPU enabled`, but it cannot force `T4` over `P100`; the canonical `vR.1` run succeeded because the live notebook runtime landed on `Tesla T4`, not because `kernel-metadata.json` selected it.
- `configs/phase1_sr3_vr1_kaggle.yaml` keeps `max_train_batches: null` by design; the training loop must interpret that as "unbounded" rather than crashing on a null comparison.
- This notebook is allowed to orchestrate scripts, inspect configs, and render outputs. It is not allowed to carry unique model-training logic.

## Canonical Result

- Readiness run: `https://wandb.ai/hndsr/hndsr-research-track/runs/pmmbvr31`
- Control run: `https://wandb.ai/hndsr/hndsr-research-track/runs/f7lc484h`
- Full train run: `https://wandb.ai/hndsr/hndsr-research-track/runs/zmfev1ot`
- Full eval run: `https://wandb.ai/hndsr/hndsr-research-track/runs/wjvc52ic`
- Control metric: bicubic `30.6039 / 0.7365`
- Full SR3 metric: `8.0865 / 0.0058`
- Conclusion: `vR.1` is valid evidence but not a promotable model baseline

## Handoff Back For Review

Return all of the following after the Kaggle run:

- The executed `vR.1_HNDSR.ipynb`
- Any Kaggle-side edits required for runtime stability
- The best checkpoint path used for evaluation
- The control, smoke, and full evaluation JSON summaries
- The comparison grid image path
- A short note about runtime duration, GPU type, and any failure modes hit during the run
