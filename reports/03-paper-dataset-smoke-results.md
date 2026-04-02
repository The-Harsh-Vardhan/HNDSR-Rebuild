# Paper Dataset Smoke Results

## What Was Run

- `ucmerced-paper-fixture-smoke`
- `aid-paper-fixture-smoke`
- `rsscn7-paper-fixture-smoke`
- `kaggle-control-smoke`

## Important Interpretation

- The three paper-dataset runs were **adapter smoke checks on generated HR-only fixture datasets**, not real benchmark runs on UCMerced, AID, or RSSCN7.
- The Kaggle control run used the real paired Kaggle `4×` dataset already present on this machine.

## Results

| Run | Dataset | Pairing | Samples | PSNR | SSIM |
| --- | --- | --- | ---: | ---: | ---: |
| `ucmerced-paper-fixture-smoke` | UCMerced fixture | `synthetic_4x` | 2 | 153.5865 | 1.0000 |
| `aid-paper-fixture-smoke` | AID fixture | `synthetic_4x` | 2 | 153.5865 | 1.0000 |
| `rsscn7-paper-fixture-smoke` | RSSCN7 fixture | `synthetic_4x` | 2 | 153.5865 | 1.0000 |
| `kaggle-control-smoke` | Kaggle 4× | `paired` | 8 | 30.6039 | 0.7365 |

## Why The Paper-Fixture Metrics Are Unrealistic

- The fixture images are intentionally simple and constant-color so the adapter path can be validated cheaply.
- Bicubic reconstruction on that synthetic content is nearly lossless, so the numbers are only a pipeline sanity check.

## Gate

- The adapter and config surface are verified.
- The paper-dataset lane is **not** benchmark-ready until real local copies of UCMerced, AID, and RSSCN7 are populated and these same smoke configs are rerun on actual data.
