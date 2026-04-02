#!/usr/bin/env python3
"""Simpler Kaggle upload: create zip from git and upload."""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.kaggle_contract import load_dataset_metadata, validate_dataset_metadata
from src.utils import REPO_ROOT, prepare_workspace_temp, resolve_kaggle_cli

DATASET_META_SRC = REPO_ROOT / "kaggle" / "dataset-metadata.json"


def run(args: list[str], **kwargs) -> subprocess.CompletedProcess:
    command = list(args)
    env = kwargs.pop("env", None)
    if command and command[0] == "kaggle":
        kaggle_prefix, kaggle_env = resolve_kaggle_cli()
        command = [*kaggle_prefix, *command[1:]]
        env = kaggle_env
    print(f"$ {' '.join(str(a) for a in command)}")
    return subprocess.run(command, capture_output=False, text=True, env=env, **kwargs)


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
    prepare_workspace_temp("kaggle_staging")

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

        print("\nUpload complete.")
        print("  Dataset: harshv777/hndsr-mini-project-code")
    finally:
        if os.environ.get("HNDSR_KEEP_KAGGLE_STAGING") == "1":
            print(f"Keeping staging directory at {work_dir}")
        elif work_dir.exists():
            shutil.rmtree(work_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
