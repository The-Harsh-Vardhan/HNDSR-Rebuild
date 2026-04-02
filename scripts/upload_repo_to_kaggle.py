#!/usr/bin/env python3
"""Simpler Kaggle upload: create zip from git and upload."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.kaggle_contract import load_dataset_metadata, validate_dataset_metadata

REPO_ROOT = Path(__file__).resolve().parents[2].parent
DATASET_META_SRC = REPO_ROOT / "research_tracks" / "hndsr_rebuild" / "kaggle" / "dataset-metadata.json"


def run(args: list[str], **kwargs) -> subprocess.CompletedProcess:
    print(f"$ {' '.join(str(a) for a in args)}")
    return subprocess.run(args, capture_output=False, text=True, **kwargs)


def ensure_safe_staging_dir(path: Path) -> None:
    """Refuse to delete or recreate directories outside the repo root."""
    resolved_repo = REPO_ROOT.resolve()
    resolved_path = path.resolve()
    if resolved_repo not in resolved_path.parents:
        raise ValueError(f"Refusing to manage staging directory outside repo root: {resolved_path}")


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--create", action="store_true")
    args = parser.parse_args()

    # Use kaggle_staging directory (not .tmp - Kaggle CLI has issues with that)
    work_dir = REPO_ROOT / "kaggle_staging"
    ensure_safe_staging_dir(work_dir)

    failures = validate_dataset_metadata(load_dataset_metadata())
    if failures:
        for failure in failures:
            print(f"ERROR: {failure}", file=sys.stderr)
        raise SystemExit(1)

    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True)

    try:
        # Copy metadata to root
        meta_target = work_dir / "dataset-metadata.json"
        shutil.copy2(DATASET_META_SRC, meta_target)
        print(f"Copied metadata to {meta_target}")

        # Create zip from git directly into Mini Project/ subfolder
        print("Creating archive from git...")
        run([
            "git", "archive",
            "--format=zip",
            "--prefix=Mini Project/",
            "--output", str(work_dir / "temp.zip"),
            "HEAD"
        ], cwd=REPO_ROOT, check=True)

        # Extract that zip in the work directory
        shutil.unpack_archive(work_dir / "temp.zip", work_dir)
        (work_dir / "temp.zip").unlink()

        print(f"Extracted repo to {work_dir / 'Mini Project'}")

        # Upload (run from within the work directory to avoid path issues)
        if args.create:
            print("Creating new dataset...")
            run([
                "kaggle", "datasets", "create",
                "-p", "."
            ], cwd=work_dir, check=True)
        else:
            print("Updating existing dataset...")
            try:
                run([
                    "kaggle", "datasets", "version",
                    "-p", ".",
                    "-m", "Auto-update from repo",
                    "--dir-mode", "zip"
                ], cwd=work_dir, check=True)
            except subprocess.CalledProcessError:
                print("Dataset doesn't exist. Creating...")
                run([
                    "kaggle", "datasets", "create",
                    "-p", "."
                ], cwd=work_dir, check=True)

        print("\n✓ Upload complete!")
        print("  Dataset: harshv777/hndsr-mini-project-code")
    finally:
        # Cleanup
        # if work_dir.exists():
        #     print(f"Cleaning up {work_dir}...")
        #     shutil.rmtree(work_dir, ignore_errors=True)
        pass


if __name__ == "__main__":
    main()
