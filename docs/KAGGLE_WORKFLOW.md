# Kaggle Workflow Guide

## Quick Start (Secret-Aware Workflow)

The default workflow now separates upload from execution because Kaggle CLI metadata does not support attaching notebook secrets:

```bash
cd <repo-root>
python scripts/kaggle_workflow.py preflight vR.1
python scripts/upload_repo_to_kaggle.py
python scripts/kaggle_workflow.py push vR.1
python scripts/kaggle_workflow.py run-editor vR.1
python scripts/kaggle_workflow.py status vR.1
```

This will:
1. Upload the notebook and metadata with `kaggle kernels push`
2. Launch the real execution from the Kaggle editor so attached secrets are available
3. Keep `status` and `pull` on the Kaggle CLI after the run starts
4. Preserve the existing monitor path for retries and log collection

Important GPU note:

- `kernel-metadata.json` can request `enable_gpu: true`, but Kaggle does not expose a metadata field to force `Tesla T4`.
- Treat `T4` as the preferred benchmark GPU and `P100` as a compatibility path only.
- The runtime now logs the assigned GPU name and uses a conservative CUDA compatibility mode when Kaggle lands on a legacy GPU such as `P100`.

W&B is now a hard gate for versioned Kaggle runs. If the notebook does not find `WANDB_API_KEY` from Kaggle secrets, the run must be declined and restarted only after the secret is configured.

### Why `run-editor` Exists

The editor-backed path is not a preference; it is a platform constraint.

- Kaggle's official kernel metadata format has no field for notebook secrets: `https://github.com/Kaggle/kaggle-api/blob/main/docs/kernels_metadata.md`
- Kaggle's own CLI issue tracker still points secret management back to `Notebook Editor -> Add-ons -> Secrets`: `https://github.com/Kaggle/kaggle-api/issues/582`

Treat `kaggle kernels push` as upload-only whenever a notebook requires `WANDB_API_KEY` or any other secret-backed runtime state.

---

## Commands Reference

| Command | Description |
|---------|-------------|
| `preflight vR.1` | Validate notebook, docs, configs, and metadata before handoff |
| `run vR.1` | Push, launch from the editor, then monitor |
| `push vR.1` | Upload only (no execution trigger) |
| `ensure-secret vR.1` | Open the editor and attach `WANDB_API_KEY` without launching a run |
| `run-editor vR.1` | Open the editor, verify the secret is attached, and launch the run |
| `status vR.1` | Check current status |
| `pull vR.1` | Download results |
| `list` | List available versions |

### Options for `run`, `run-editor`, and `ensure-secret`:
- `--interval 60` - Check every N seconds (default: 60)
- `--max-retries 3` - Max auto-fix attempts (default: 3)
- `--profile-dir <path>` - Persistent browser profile used for Kaggle login/session reuse
- `--channel msedge` - Browser channel passed to Playwright (default on Windows)
- `--dry-run` - Print the planned browser command without launching it

---

## Metadata Contract

Two tracked metadata files define the Kaggle handoff contract:

- `notebooks/versions/kernel-metadata.json`
- `kaggle/dataset-metadata.json`

Rules:

1. `kernel-metadata.json` is the only source of truth for the current Kaggle kernel slug, title, notebook file, and attached datasets.
2. `code_file` must match the notebook version exactly, for example `vR.1_HNDSR.ipynb`.
3. The code dataset source must remain `harshv777/hndsr-mini-project-code`.
4. `dataset-metadata.json` is the only source of truth for packaging the repo dataset upload.
5. Update metadata before pushing a new notebook version, not after a failed Kaggle run.

Validate locally before a handoff:

```bash
python scripts/kaggle_workflow.py preflight vR.1
```

Equivalent direct validator call:

```bash
python scripts/validate_notebook_version.py ^
  --version vR.1 ^
  --notebook notebooks/versions/vR.1_HNDSR.ipynb ^
  --doc docs/notebooks/vR.1_HNDSR.md ^
  --review reports/reviews/vR.1_HNDSR.review.md ^
  --config configs/phase1_sr3_vr1_kaggle.yaml ^
  --smoke-config configs/phase1_sr3_vr1_smoke.yaml ^
  --control-config configs/phase0_bicubic_vr1_kaggle_control.yaml
```

---

## Auto-Fix Capabilities

The monitor detects these errors and attempts fixes:

| Error | Auto-Fix |
|-------|----------|
| "Expected rebuild track under repo root" | Prompts to update dataset |
| "ModuleNotFoundError" | Shows which module to pip install |
| "CUDA out of memory" | Suggests reducing batch size |
| "FileNotFoundError: config" | Prompts to update dataset |

---

## Running Future Ablations (vR.2, vR.3, etc.)

### Step 1: Make Code Changes Locally
Edit configs, models, or scripts in your repo. Keep the change inside the current version unless the benchmark contract itself changes.

### Step 2: Update Repo Dataset
```bash
cd <repo-root>
python scripts/upload_repo_to_kaggle.py
```

Then:
1. If the dataset does not exist yet, re-run with `--create`
2. Confirm the updated version appears at `harshv777/hndsr-mini-project-code`
3. Keep the dataset ID unchanged across notebook versions
4. Re-upload the repo dataset after any same-version Kaggle runtime patch if the notebook still delegates to repo-owned scripts under `/kaggle/input`
5. The runtime loader now resolves Kaggle image mounts automatically when `HR_0.5m` and `LR_2m` are wrapped inside duplicated directories under `/kaggle/input`

### Step 3: Create New Notebook Version
1. Finish the current version review first.
2. Scaffold the next version:
```bash
python scripts/scaffold_version.py --from-version vR.1 --to-version vR.2 --activate-kaggle
```
3. Update configs or model changes only after the scaffold exists.
4. Commit the scaffold before deeper edits.

### Step 4: Update Kernel Metadata
Edit `notebooks/versions/kernel-metadata.json`:
```json
{
  "id": "harshv777/vr-2-hndsr-sr3-baseline",  // Update slug
  "title": "vR.2 HNDSR SR3 Baseline",          // Update title
  "code_file": "vR.2_HNDSR.ipynb",             // Update file
  ...
}
```

### Step 5: Push to Kaggle
```bash
python scripts/kaggle_workflow.py push vR.2
```

### Step 6: Monitor & Pull
```bash
# Check status
python scripts/kaggle_workflow.py status vR.2

# Pull results when done
python scripts/kaggle_workflow.py pull vR.2
```

---

## Troubleshooting

### "Expected rebuild track under repo root" Error
The repo dataset wasn't attached. Check:
1. Does `kernel-metadata.json` include `harshv777/hndsr-mini-project-code` in `dataset_sources`?
2. Did `upload_repo_to_kaggle.py` finish successfully for the current repo state?
3. Push the kernel again: `kaggle kernels push -p "notebooks/versions"`

### "Read-only file system" Under `/kaggle/input/.../artifacts`
The notebook or validator is still using the attached repo dataset directly instead of a writable copy under `/kaggle/working`.
1. Re-upload `harshv777/hndsr-mini-project-code` from the latest repo commit.
2. Re-push the same notebook version after the dataset upload finishes.
3. Confirm the runtime diagnostics show the repo under `/kaggle/working/HNDSR-Rebuild` before training starts.

### "No paired images found in data/kaggle_4x/HR_0.5m and data/kaggle_4x/LR_2m"
Kaggle mounted the image dataset, but not in the flat repo-local layout.
1. Stay on `vR.1`; this is a Kaggle plumbing issue, not a new research version.
2. Re-upload the latest repo dataset so the runtime loader patch is attached.
3. Re-push the same notebook version after the dataset upload finishes.

### "CUDA error: no kernel image is available for execution on the device"
Kaggle exposed a GPU that the bundled PyTorch build cannot actually execute.
1. Stay on `vR.1`; this is a runtime compatibility issue, not a new research version.
2. Do not fake a metadata-level `T4` selection; Kaggle does not support it.
3. Prefer the runtime compatibility policy first: keep GPU enabled, log the assigned device, and let the scripts switch into `cuda-compat` mode on older GPUs.
4. Only attempt a runtime torch reinstall if compatibility mode still fails and the phase gate truly requires GPU throughput.

### "Dataset not found" Error
Do not invent a new dataset name. Fix `kaggle/dataset-metadata.json` and `kernel-metadata.json` so both reference `harshv777/hndsr-mini-project-code`.

### Kernel Stuck in "RUNNING"
- Training takes 30-60 minutes for full runs
- Smoke runs take ~5-10 minutes
- Check logs: `kaggle kernels output harshv777/vr-X-hndsr-sr3-baseline`

### W&B Not Logging
1. Verify the Kaggle secret `WANDB_API_KEY` exists.
2. Use `python scripts/kaggle_workflow.py ensure-secret vR.1` to attach the secret to the notebook editor before the next run.
3. Check notebook cell output for "authenticated online tracking is now enforced".
4. If the key is missing or tracking stays offline, decline the run and redo it. Do not accept the run as valid evidence.

### CLI Push Works But Secrets Do Not
This is the current Kaggle limitation that motivated the editor automation path.
1. Use `push` for upload only.
2. Use `run-editor` for the actual launch.
3. Keep the same persistent browser profile so Kaggle auth and notebook-level secret attachment survive between runs.

---

## Quick Reference

| Command | Action |
|---------|--------|
| `python scripts/kaggle_workflow.py status vR.1` | Check run status |
| `python scripts/kaggle_workflow.py pull vR.1` | Download results |
| `python scripts/kaggle_workflow.py list` | List available versions |
| `python scripts/upload_repo_to_kaggle.py` | Update repo dataset |
| `kaggle datasets list --mine` | List your datasets |
| `kaggle kernels list --mine \| grep vr` | List your kernels |

---

## Default Workflow (Ablation Study)

1. **Preflight** → `python scripts/kaggle_workflow.py preflight vR.X`
2. **Upload** → `python scripts/upload_repo_to_kaggle.py`
3. **Push** → `python scripts/kaggle_workflow.py push vR.X`
4. **Editor Run** → `python scripts/kaggle_workflow.py run-editor vR.X`
5. **Wait** → 30-60 minutes for full training
6. **Pull** → `python scripts/kaggle_workflow.py pull vR.X`
7. **Log** → Update `benchmarks/kaggle_runs.tsv`
8. **Review** → Update `reports/reviews/<stem>.review.md`
9. **Decide** → Keep, patch, or promote
