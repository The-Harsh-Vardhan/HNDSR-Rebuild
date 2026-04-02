# HNDSR Rebuild Kickoff

## Intent

- Rebuild the research lane in an isolated folder.
- Keep production untouched until a new baseline is verified.
- Use W&B as the only experiment tracker in the new lane.
- Honor the paper-dataset lane first: UCMerced, AID, and RSSCN7 before deeper Kaggle-only work.

## Phase Ladder

1. Bicubic bootstrap and dataset parity checks
2. Paper-dataset adapter checks for UCMerced, AID, and RSSCN7
3. SR3-style conditional diffusion baseline
4. Latent diffusion baseline
5. Neural-operator baseline and hybrid merge

## Gate Policy

- Do not promote a phase unless it beats bicubic on the tracked validation pack.
- Every promoted phase must export metrics JSON and sample strips for the fixed smoke pack.
- Notebook outputs are summaries only; scripts remain the source of truth.
