# HNDSR Research Program

This repo follows a constrained research loop inspired by Karpathy's `autoresearch` pattern: keep the benchmark contract stable, limit the editable surface for each version, and log every keep, discard, and failure explicitly.

## Fixed Contract For The Current Cycle

The current active cycle is `vR.1`.

- Active notebook: `notebooks/versions/vR.1_HNDSR.ipynb`
- Paired doc: `docs/notebooks/vR.1_HNDSR.md`
- Paired review: `reports/reviews/vR.1_HNDSR.review.md`
- Full config: `configs/phase1_sr3_vr1_kaggle.yaml`
- Smoke config: `configs/phase1_sr3_vr1_smoke.yaml`
- Control config: `configs/phase0_bicubic_vr1_kaggle_control.yaml`
- Fixed control lane: Kaggle `4x-satellite-image-super-resolution`
- Fixed scale: `4x`
- Fixed comparison artifacts: control metrics, smoke metrics, full metrics, comparison grid, and best checkpoint path

Do not change the benchmark contract inside the same notebook version unless the change is a runtime repair that keeps the benchmark meaning intact.

## Editable Surface

Within an active version, edits are allowed in:

- the versioned notebook runtime cells
- its paired markdown doc
- its paired review doc
- configs used by that version
- scripts and source files required to fix runtime, logging, packaging, or model behavior

Out of bounds for a runtime-only patch:

- renaming the version
- changing the version lineage
- silently changing the evaluation story
- silently changing dataset semantics
- silently changing metric definitions

If one of those changes is required, fork a new notebook version instead of patching in place.

## Kaggle Loop

1. Run preflight:
   `python scripts/kaggle_workflow.py preflight vR.1`
2. Update the Kaggle code dataset:
   `python scripts/upload_repo_to_kaggle.py`
3. Push and monitor:
   `python scripts/kaggle_workflow.py run vR.1`
4. Pull outputs:
   `python scripts/kaggle_workflow.py pull vR.1`
5. Sync the executed notebook and returned artifacts into the repo.
6. Update `benchmarks/kaggle_runs.tsv`.
7. Write findings into `reports/reviews/vR.1_HNDSR.review.md`.
8. Decide:
   - `keep` and freeze the version
   - `patch` the same version for runtime-only fixes
   - `promote` to the next version

## Keep, Patch, Promote

- `keep`: the run is valid, artifacts are complete, and the version tells a truthful story.
- `patch`: the run found a runtime or packaging defect that does not justify a new version.
- `promote`: the next change alters model, optimizer, loss, dataset protocol, checkpoint source, or evaluation contract.

## Experiment Logging

The tracked experiment log is `benchmarks/kaggle_runs.tsv`.

Every Kaggle cycle should log:

- version
- kernel id
- status
- git commit
- key metrics
- decision
- notes about crashes, runtime constraints, or misleading assumptions

## Failure Policy

- Preserve broken but informative Kaggle-returned states with a commit before fixing them.
- Do not erase a failed run from the notebook history or the experiment log.
- If a run crashes for a trivial bug, fix it and rerun.
- If a run fails because the idea is weak or misleading, log the failure and move on.

## Next Version Rule

Do not create `vR.2` until:

- `vR.1` has been executed on Kaggle
- the review doc is populated
- the experiment log has been updated
- the promotion decision says a new version is justified
