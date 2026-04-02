# Kaggle Workflow Guide

## Quick Start (Default Workflow)

The default workflow pushes and monitors automatically with auto-fix:

```bash
cd <repo-root>
python scripts/kaggle_workflow.py preflight vR.1
python scripts/upload_repo_to_kaggle.py
python scripts/kaggle_workflow.py run vR.1
```

This will:
1. Push the notebook to Kaggle
2. Monitor status every 60 seconds
3. On failure: fetch error, attempt auto-fix, retry (up to 3 times)
4. On success: notify you to pull results

---

## Commands Reference

| Command | Description |
|---------|-------------|
| `preflight vR.1` | Validate notebook, docs, configs, and metadata before handoff |
| `run vR.1` | **DEFAULT**: Push + monitor with auto-fix |
| `push vR.1` | Push only (no monitoring) |
| `status vR.1` | Check current status |
| `pull vR.1` | Download results |
| `list` | List available versions |

### Options for `run`:
- `--interval 60` - Check every N seconds (default: 60)
- `--max-retries 3` - Max auto-fix attempts (default: 3)

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

### "Dataset not found" Error
Do not invent a new dataset name. Fix `kaggle/dataset-metadata.json` and `kernel-metadata.json` so both reference `harshv777/hndsr-mini-project-code`.

### Kernel Stuck in "RUNNING"
- Training takes 30-60 minutes for full runs
- Smoke runs take ~5-10 minutes
- Check logs: `kaggle kernels output harshv777/vr-X-hndsr-sr3-baseline`

### W&B Not Logging
1. Verify secret was added in Kaggle UI
2. Check notebook cell output for "W&B key detected"
3. If offline mode is okay, skip this

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
4. **Wait** → 30-60 minutes for full training
5. **Pull** → `python scripts/kaggle_workflow.py pull vR.X`
6. **Log** → Update `benchmarks/kaggle_runs.tsv`
7. **Review** → Update `reports/reviews/<stem>.review.md`
8. **Decide** → Keep, patch, or promote
