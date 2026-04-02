# Paper Dataset Adapter

## Intent

- Make the rebuild track paper-dataset-first without deleting the Kaggle control lane.
- Support HR-only remote-sensing datasets through deterministic synthetic `4×` LR generation.
- Keep the train and eval scripts unchanged above the dataset boundary.

## Implemented Contract

- `dataset.family`: `paper` or `kaggle`
- `dataset.name`: `ucmerced`, `aid`, `rsscn7`, or `kaggle_4x`
- `dataset.pairing_mode`: `synthetic_4x` or `paired`

## Current Local State

- Kaggle `4×` paired paths remain wired and runnable.
- Candidate paper-dataset roots are configured under `configs/base.yaml`.
- The implementation search did **not** find real local copies of `UCMerced`, `AID`, or `RSSCN7` on this machine during the build step.

## What Was Verified

- Deterministic split generation for each paper dataset name through test fixtures.
- Deterministic synthetic `4×` LR generation and filename traceability through test fixtures.
- Kaggle paired-lane compatibility remains covered by tests.

## Promotion Rule

- Do not treat the paper-dataset lane as benchmark-ready until the real dataset roots are populated and the smoke configs run on actual data.
