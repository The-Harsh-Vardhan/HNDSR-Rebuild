# vR.2 HNDSR

## Objective

`vR.2 HNDSR` is the supervised reset after the failed `vR.1` SR3 baseline. Its job is to prove that the data path, metrics, loss, checkpointing, and Kaggle handoff can produce a sane trainable super-resolution baseline before this rebuild track returns to diffusion.

Current state:

- Kaggle/W&B contract: scaffolded and ready for authenticated runs
- Hardware policy: prefer `Tesla T4`, allow `Tesla P100` in logged compatibility mode
- Model outcome: pending first canonical run
- Promotion target: beat the frozen `vR.1` SR3 baseline and produce qualitatively coherent outputs

## Scope

- Dataset lane: Kaggle `4x-satellite-image-super-resolution`
- Model lane: scratch `supervised_residual` baseline from `src/models.py`
- Control lane: bicubic evaluation using the same Kaggle split and smoke pack
- Tracker mode: authenticated `W&B online` only; decline the run if the Kaggle secret is missing
- Execution path: `kaggle kernels push` for upload, Kaggle editor launch for the actual secret-backed run

## Config Contract

- Full training config: `configs/phase2_supervised_vr2_kaggle.yaml`
- Smoke training config: `configs/phase2_supervised_vr2_smoke.yaml`
- Bicubic control config: `configs/phase0_bicubic_vr2_kaggle_control.yaml`
- Fixed scale: `4x`
- Run names used in notebook:
  - `vR.2-control`
  - `vR.2-smoke`
  - `vR.2-smoke-eval`
  - `vR.2-train`
  - `vR.2-eval`

## Kaggle Run Guide

1. Open `notebooks/versions/vR.2_HNDSR.ipynb`.
2. Attach both datasets declared in `notebooks/versions/kernel-metadata.json`:
   - `cristobaltudela/4x-satellite-image-super-resolution`
   - `harshv777/hndsr-mini-project-code`
3. Run `python scripts/kaggle_workflow.py preflight vR.2` locally before handing the notebook to Kaggle.
4. Push the latest repo snapshot with `python scripts/upload_repo_to_kaggle.py`, then upload the notebook metadata with `python scripts/kaggle_workflow.py push vR.2`.
5. Launch the actual run with `python scripts/kaggle_workflow.py run-editor vR.2`. Do not rely on CLI-triggered execution when `WANDB_API_KEY` is required.
6. Run the runtime diagnostics cells first and confirm the notebook finds the repo under one of the mounted `/kaggle/input/*` datasets, or extracts a mounted `Mini Project.zip` archive into `/kaggle/working/HNDSR-Rebuild`, before training.
7. Re-run `python scripts/upload_repo_to_kaggle.py` after any same-version Kaggle runtime patch so the attached repo dataset matches the notebook shell.
8. Confirm CUDA visibility if a GPU runtime is enabled.
9. Confirm the runtime cell prints the assigned GPU name early. If Kaggle lands on `Tesla P100`, keep the run but note that it is in compatibility mode rather than preferred benchmark hardware.
10. Confirm the W&B setup cell prints that authenticated online tracking is enforced. If it does not, stop and fix Kaggle secrets before continuing.
11. Run the readiness validator cell before any training cell.
12. Run the bicubic control evaluation to confirm the dataset and metrics path.
13. Run the smoke training cell to confirm the supervised checkpoint, metric summaries, and sample exports are coherent.
14. Run the full training and full evaluation cells only after the smoke path succeeds.
15. Export the executed notebook, the generated metrics JSON, the comparison grid, and the best checkpoint path back into the repo workflow for review.

## Expected Artifacts

- Control eval summary JSON under `artifacts/vR.2-control/`
- Smoke checkpoint and metrics under `artifacts/vR.2-smoke/`
- Full training checkpoint and metrics under `artifacts/vR.2-train/`
- Full evaluation summary and image strips under `artifacts/vR.2-eval/`
- Authenticated W&B run links plus local tracker records under each run's `tracker/` directory

## Known Constraints

- `vR.2` stays on the Kaggle control lane even though the broader rebuild track is paper-first.
- `vR.2` now rejects Kaggle execution unless the `WANDB_API_KEY` secret is available and online tracking is enforced before the first validator or training command.
- Kaggle CLI upload metadata does not currently expose notebook secrets, so the authoritative run launch must come from the Kaggle editor path after the secret is attached.
- The notebook now checks both Kaggle working-directory mounts and the attached code-dataset mount before asserting the repo layout.
- The attached Kaggle code dataset may arrive under nested private-dataset paths such as `/kaggle/input/datasets/<owner>/<slug>` and may contain `Mini Project.zip`; `vR.2` now recurses through the Kaggle input tree and copies any discovered repo from the read-only input mount into `/kaggle/working/HNDSR-Rebuild` before validation or training writes artifacts.
- The runtime scripts now auto-resolve the Kaggle image dataset even when Kaggle wraps the image folders inside duplicated directories such as `/kaggle/input/4x-satellite-image-super-resolution/HR_0.5m/HR_0.5m` and `/LR_2m/LR_2m`.
- Kaggle metadata can request `GPU enabled`, but it cannot force `T4` over `P100`; the notebook and scripts therefore log the assigned GPU and mark `P100` as compatibility mode rather than pretending metadata can select hardware.
- `configs/phase2_supervised_vr2_kaggle.yaml` keeps `max_train_batches: null` by design; the training loop now interprets that as "unbounded" rather than crashing on a null comparison.
- `vR.2` is deliberately a supervised sanity reset. Do not reintroduce diffusion work into this version; that would violate the review decision that followed the failed `vR.1` baseline.
- This notebook is allowed to orchestrate scripts, inspect configs, and render outputs. It is not allowed to carry unique model-training logic.

## Success Criteria

- The first canonical `vR.2` run must be authenticated in W&B.
- `vR.2` must materially beat the frozen `vR.1` SR3 result on both PSNR and SSIM.
- The exported comparison strips must look like real super-resolution outputs rather than diffusion noise.
- The review decision stays at `patch-vR.2` until the supervised baseline at least approaches the bicubic control.

## Handoff Back For Review

Return all of the following after the Kaggle run:

- The executed `vR.2_HNDSR.ipynb`
- Any Kaggle-side edits required for runtime stability
- The best checkpoint path used for evaluation
- The control, smoke, and full evaluation JSON summaries
- The comparison grid image path
- A short note about runtime duration, GPU type, and any failure modes hit during the run
