# Bootstrap Results

## Scope

- Dataset and evaluation parity through the isolated track
- Bicubic bootstrap on the fixed 8-sample validation smoke pack
- One-epoch SR3-style smoke train and evaluation on CPU

## Run Outputs

- Bicubic bootstrap run: `phase0-bicubic-smoke`
- SR3 smoke train run: `phase1-sr3-smoke`
- SR3 smoke eval run: `phase1-sr3-smoke-eval`

## Measured Results

| Run | Samples | PSNR | SSIM | Notes |
| --- | ---: | ---: | ---: | --- |
| Bicubic bootstrap | 8 | 30.6039 | 0.7365 | Strong fixed-pack reference for future phases |
| SR3 smoke eval | 8 | 7.9618 | 0.0072 | One epoch, four train batches, ten inference steps, CPU only |

## Training Snapshot

- SR3 smoke train loss: `0.9821`
- SR3 smoke val loss: `0.9096`
- SR3 smoke quick val PSNR: `7.8480`
- Saved checkpoint: `artifacts/phase1-sr3-smoke/checkpoints/sr3_smoke.pt`

## Interpretation

- The new track is real: training, checkpointing, evaluation, and sample export all execute end to end.
- The SR3 smoke result is intentionally poor because the run is compute-starved. That is acceptable for the bootstrap slice because it verifies the research loop without faking quality.
- Bicubic is now the explicit baseline to beat before moving deeper into SR3 ablations or the latent/operator branches.

## Known Environment Noise

- W&B bootstrap works in offline mode, but the machine still emits Windows temp-directory cleanup warnings from W&B internals.
- Pytest also needs `--basetemp` inside the workspace because the system temp path has permission issues.
