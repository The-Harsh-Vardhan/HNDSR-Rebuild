# vR.1 HNDSR Review

## Status

- State: frozen failed baseline
- Lineage: scratch (`vR.x`)
- Scope: first immutable SR3 Kaggle notebook for the rebuild track
- Decision owner: standalone `HNDSR-Rebuild` repo
- Canonical evidence: `notebooks/runs/vr-1-hndsr-sr3-baseline-run-01.ipynb`

## Run Intake

- Returned notebook path: `notebooks/runs/vr-1-hndsr-sr3-baseline-run-01.ipynb`
- Kaggle notebook: `harshv777/vr-1-hndsr-sr3-baseline`
- Kaggle runtime: interactive notebook run with W&B-authenticated editor launch
- GPU or CPU: `cuda` on `Tesla T4`
- Readiness W&B run: `https://wandb.ai/hndsr/hndsr-research-track/runs/pmmbvr31`
- Control W&B run: `https://wandb.ai/hndsr/hndsr-research-track/runs/f7lc484h`
- Smoke-train W&B run: `https://wandb.ai/hndsr/hndsr-research-track/runs/5p6t48cn`
- Smoke-eval W&B run: `https://wandb.ai/hndsr/hndsr-research-track/runs/x3srq983`
- Full-train W&B run: `https://wandb.ai/hndsr/hndsr-research-track/runs/zmfev1ot`
- Full-eval W&B run: `https://wandb.ai/hndsr/hndsr-research-track/runs/wjvc52ic`
- Best smoke checkpoint path: `/kaggle/working/HNDSR-Rebuild/artifacts/vR.1-smoke/checkpoints/vR.1_sr3_smoke.pt`
- Best full checkpoint path: `/kaggle/working/HNDSR-Rebuild/artifacts/vR.1-train/checkpoints/vR.1_sr3_best.pt`
- Control summary: bicubic `PSNR 30.603863916799494 / SSIM 0.7364999055862427`
- Smoke summary: SR3 `PSNR 7.951168545245405 / SSIM 0.005284100800054148`
- Full evaluation summary: SR3 `PSNR 8.086530605734985 / SSIM 0.0057636301789898425`

## Audit Checklist

- Notebook structure stayed aligned with the contract.
- Script calls remained thin and repo-relative.
- Metrics, checkpoint, and sample artifact paths are all traceable.
- W&B tracker state is explicit and reproducible.
- Kaggle-only fixes were mirrored back into repo code or docs before the canonical run.

## Findings

1. Severe: the trainable SR3 lane is non-competitive against the bicubic control, so `vR.1` proves the workflow but fails the model objective.
   Evidence: the executed run reports bicubic at `30.6039 / 0.7365`, while the final SR3 eval reports `8.0865 / 0.0058`.
   Impact: the first scratch trainable baseline is not merely under-tuned; it is catastrophically worse than the no-learning control and therefore not promotable.
2. High: the current `vR.1` hypothesis was wrong, and the notebook disproves it with clean evidence.
   Evidence: the notebook states that a conservative SR3 baseline should beat bicubic qualitatively if the pipeline is wired correctly, but the completed run shows the opposite on both PSNR and SSIM after successful T4 training.
   Impact: the next version should not spend more Kaggle budget on another near-identical diffusion retry.
3. High: training loss improved while image quality stayed unusably bad, which is a contract-level smell in the current SR3 setup.
   Evidence: full training drove `val_loss` down to `0.03937`, yet `val_psnr` remained around `8.1` and the final eval SSIM stayed near zero.
   Impact: the current objective and model family are not aligned with the repo’s actual SR goal on this dataset.
4. Medium: `vR.1` proved the secret-aware W&B and Kaggle handoff path, which means future failures are now model failures rather than platform excuses.
   Evidence: the completed run shows authenticated W&B links for readiness, control, smoke, train, and eval, all on `cuda` with an explicit `Tesla T4`.
   Impact: the infrastructure is good enough to move to a saner baseline rather than continuing to debug plumbing.
5. Medium: the older local `artifacts/kaggle_outputs/vR.1` bundle is mixed stale history and should not be used as review evidence.
   Evidence: pulled summaries under that tree still report CPU/offline values from earlier retries, while the executed notebook shows the canonical T4/W&B-backed run.
   Impact: the executed notebook is the source of truth for `vR.1` freeze decisions.

## Roast

The good news is that `vR.1` finally stopped lying about infrastructure. The bad news is that once the run became real, the model face-planted. This baseline spent a full authenticated T4 run proving that the current SR3 setup can optimize noise loss and still generate outputs so weak that bicubic beats it by more than twenty PSNR points. That is not a “small tuning gap.” That is the wrong first trainable baseline for this repo.

The notebook did its job. The model did not. `vR.1` is a workflow success and a research failure. Treating this as “almost there” would be self-inflicted confusion. The sane move is to freeze the evidence, stop pretending diffusion is the right first control-lane learner here, and reset `vR.2` to a supervised SR baseline that can actually prove the data, metrics, and training loop are coherent.

## Promotion Decision

- Decision: do not promote the SR3 approach; freeze `vR.1` as a failed but valid baseline
- Freeze current version, patch in place, or fork next version: freeze `vR.1`, fork `vR.2`
- Rationale: `vR.1` completed cleanly on T4 with authenticated W&B tracking, so the remaining failure is model quality, not Kaggle plumbing. The next version should reset to a supervised scratch baseline before any further diffusion work.
