#!/usr/bin/env python3
"""Kaggle notebook workflow helper for HNDSR ablation studies.

Usage:
    python kaggle_workflow.py run vR.1         # Push and monitor (DEFAULT)
    python kaggle_workflow.py push vR.1        # Push only (no monitoring)
    python kaggle_workflow.py status vR.1      # Check run status
    python kaggle_workflow.py pull vR.1        # Pull results
    python kaggle_workflow.py list             # List available versions
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.kaggle_contract import load_kernel_metadata, validate_kernel_metadata

REPO_ROOT = Path(__file__).resolve().parents[2].parent
NOTEBOOKS_DIR = REPO_ROOT / "research_tracks" / "hndsr_rebuild" / "notebooks" / "versions"
RESULTS_DIR = REPO_ROOT / "research_tracks" / "hndsr_rebuild" / "artifacts" / "kaggle_outputs"
SCRIPTS_DIR = Path(__file__).parent


def run_cmd(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    print(f"$ {' '.join(args)}")
    return subprocess.run(args, check=check)


def load_validated_kernel_metadata(version: str) -> dict:
    metadata = load_kernel_metadata()
    failures = validate_kernel_metadata(version, metadata)
    if failures:
        for failure in failures:
            print(f"ERROR: {failure}")
        sys.exit(1)
    return metadata


def cmd_push(version: str) -> bool:
    """Push notebook to Kaggle and start execution. Returns True if successful."""
    notebook_path = NOTEBOOKS_DIR / f"{version}_HNDSR.ipynb"

    if not notebook_path.exists():
        print(f"ERROR: Notebook not found: {notebook_path}")
        return False

    metadata = load_validated_kernel_metadata(version)
    kernel_id = metadata.get("id", "")
    if kernel_id:
        print(f"Pushing {version} to Kaggle (ID: {kernel_id})...")
    else:
        print(f"Pushing {version} to Kaggle (new kernel)...")

    result = run_cmd(["kaggle", "kernels", "push", "-p", str(NOTEBOOKS_DIR)], check=False)
    return result.returncode == 0


def cmd_run(version: str, interval: int = 60, max_retries: int = 3) -> None:
    """Push notebook and start monitoring with auto-fix."""
    print(f"=== Running {version} with auto-monitoring ===\n")

    # Push first
    if not cmd_push(version):
        print("ERROR: Failed to push notebook")
        sys.exit(1)

    print("\nStarting monitor...")
    print("-" * 50)

    # Start the monitor script
    monitor_script = SCRIPTS_DIR / "monitor_kaggle.py"
    result = subprocess.run([
        sys.executable, str(monitor_script),
        version,
        "--interval", str(interval),
        "--max-retries", str(max_retries),
    ])
    sys.exit(result.returncode)


def cmd_status(version: str) -> None:
    """Check execution status of a notebook."""
    metadata = load_validated_kernel_metadata(version)
    kernel_id = metadata.get("id", "")
    if not kernel_id:
        print("ERROR: No kernel ID found in metadata")
        sys.exit(1)
    run_cmd(["kaggle", "kernels", "status", kernel_id])


def cmd_pull(version: str) -> None:
    """Pull outputs from a completed notebook run."""
    metadata = load_validated_kernel_metadata(version)
    kernel_id = metadata.get("id", "")
    if not kernel_id:
        print("ERROR: No kernel ID found in metadata")
        sys.exit(1)

    output_dir = RESULTS_DIR / version
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Pulling outputs from {kernel_id} to {output_dir}...")
    run_cmd(["kaggle", "kernels", "output", kernel_id, "-p", str(output_dir)])


def cmd_list() -> None:
    """List available notebook versions."""
    print("Available notebook versions:")
    for nb in sorted(NOTEBOOKS_DIR.glob("vR*_HNDSR.ipynb")):
        version = nb.stem.replace("_HNDSR", "")
        print(f"  {version}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Kaggle workflow helper")
    parser.add_argument("command", choices=["run", "push", "status", "pull", "list"],
                        help="run=push+monitor, push=push only")
    parser.add_argument("version", nargs="?", help="Notebook version (e.g., vR.1)")
    parser.add_argument("--interval", type=int, default=60, help="Monitor check interval (default: 60s)")
    parser.add_argument("--max-retries", type=int, default=3, help="Max auto-fix retries (default: 3)")
    args = parser.parse_args()

    if args.command == "list":
        cmd_list()
    elif args.version is None:
        parser.error(f"'{args.command}' requires a version argument")
    elif args.command == "run":
        cmd_run(args.version, args.interval, args.max_retries)
    elif args.command == "push":
        if not cmd_push(args.version):
            sys.exit(1)
    elif args.command == "status":
        cmd_status(args.version)
    elif args.command == "pull":
        cmd_pull(args.version)


if __name__ == "__main__":
    main()
