#!/usr/bin/env python3
"""Kaggle notebook workflow helper for HNDSR ablation studies.

Usage:
    python kaggle_workflow.py preflight vR.1     # Validate the notebook handoff surface
    python kaggle_workflow.py run vR.1           # Push, launch from editor, and monitor
    python kaggle_workflow.py push vR.1          # Upload only
    python kaggle_workflow.py ensure-secret vR.1
    python kaggle_workflow.py run-editor vR.1
    python kaggle_workflow.py status vR.1
    python kaggle_workflow.py pull vR.1
    python kaggle_workflow.py list
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.kaggle_contract import CODE_DATASET_ID, load_kernel_metadata, validate_kernel_metadata
from src.utils import (
    REPO_ROOT,
    ensure_dir,
    resolve_kaggle_cli,
    resolve_node_executable,
    resolve_npx_executable,
    resolve_python_executable,
)
from src.versioning import default_contract_paths, notebook_stem

NOTEBOOKS_DIR = REPO_ROOT / "notebooks" / "versions"
RESULTS_DIR = REPO_ROOT / "artifacts" / "kaggle_outputs"
PLAYWRIGHT_DIR = REPO_ROOT / "artifacts" / "playwright"
SCRIPTS_DIR = Path(__file__).parent
WORKFLOW_PYTHON = resolve_python_executable()
EDITOR_SECRET_NAME = "WANDB_API_KEY"


def run_cmd(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a subprocess, resolving the Kaggle CLI when needed."""
    command = args
    env = None
    if args and args[0] == "kaggle":
        kaggle_prefix, env = resolve_kaggle_cli()
        command = [*kaggle_prefix, *args[1:]]
    print(f"$ {' '.join(command)}")
    return subprocess.run(command, check=check, env=env)


def load_validated_kernel_metadata(version: str) -> dict:
    """Load and validate the tracked Kaggle kernel metadata for a version."""
    metadata = load_kernel_metadata()
    failures = validate_kernel_metadata(version, metadata)
    if failures:
        for failure in failures:
            print(f"ERROR: {failure}")
        sys.exit(1)
    return metadata


def cmd_preflight(version: str) -> None:
    """Validate the notebook contract and print the Kaggle handoff surface."""
    contract = default_contract_paths(version)
    for label, relative_path in contract.items():
        resolved = REPO_ROOT / relative_path
        if not resolved.exists():
            print(f"ERROR: Missing {label} file: {resolved}")
            sys.exit(1)

    result = subprocess.run(
        [
            str(WORKFLOW_PYTHON),
            str(SCRIPTS_DIR / "validate_notebook_version.py"),
            "--version",
            version,
            "--notebook",
            str(contract["notebook"]),
            "--doc",
            str(contract["doc"]),
            "--review",
            str(contract["review"]),
            "--config",
            str(contract["full_config"]),
            "--smoke-config",
            str(contract["smoke_config"]),
            "--control-config",
            str(contract["control_config"]),
        ],
        cwd=REPO_ROOT,
    )
    if result.returncode != 0:
        sys.exit(result.returncode)

    metadata = load_validated_kernel_metadata(version)
    print("")
    print(f"Notebook stem: {notebook_stem(version)}")
    print(f"Kernel ID: {metadata['id']}")
    print(f"Code dataset source: {CODE_DATASET_ID}")
    print(f"Kaggle notebook directory: {NOTEBOOKS_DIR}")
    if Path(sys.executable).resolve() != WORKFLOW_PYTHON.resolve():
        print(f"Validation interpreter: {WORKFLOW_PYTHON}")


def cmd_push(version: str) -> bool:
    """Push notebook metadata and code to Kaggle. Returns True if successful."""
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


def build_editor_runner_command(
    version: str,
    action: str,
    *,
    profile_dir: Path,
    debug_dir: Path,
    channel: str | None,
    headless: bool,
    timeout_ms: int,
    dry_run: bool,
) -> list[str]:
    """Build the Node/Playwright command for secret-aware Kaggle editor automation."""
    metadata = load_validated_kernel_metadata(version)
    command = [
        resolve_npx_executable(),
        "--yes",
        "--package",
        "playwright",
        resolve_node_executable(),
        str(SCRIPTS_DIR / "kaggle_editor_runner.mjs"),
        "--mode",
        action,
        "--kernel-id",
        metadata["id"],
        "--secret-name",
        EDITOR_SECRET_NAME,
        "--profile-dir",
        str(profile_dir),
        "--debug-dir",
        str(debug_dir),
        "--timeout-ms",
        str(timeout_ms),
    ]
    if channel:
        command.extend(["--channel", channel])
    command.append("--headless" if headless else "--headed")
    if dry_run:
        command.append("--dry-run")
    return command


def _default_browser_channel() -> str | None:
    if os.name == "nt":
        return "msedge"
    return None


def _run_editor_action(
    version: str,
    action: str,
    *,
    profile_dir: str | None,
    channel: str | None,
    headless: bool,
    timeout_ms: int,
    dry_run: bool,
) -> bool:
    resolved_profile = Path(profile_dir) if profile_dir else PLAYWRIGHT_DIR / "kaggle-profile"
    resolved_debug = ensure_dir(PLAYWRIGHT_DIR / version)
    ensure_dir(resolved_profile)

    command = build_editor_runner_command(
        version,
        action,
        profile_dir=resolved_profile,
        debug_dir=resolved_debug,
        channel=channel or _default_browser_channel(),
        headless=headless,
        timeout_ms=timeout_ms,
        dry_run=dry_run,
    )
    print(f"{action} profile: {resolved_profile}")
    print(f"{action} debug artifacts: {resolved_debug}")
    print(f"$ {' '.join(command)}")
    if dry_run:
        return True
    result = subprocess.run(command, cwd=REPO_ROOT, check=False)
    return result.returncode == 0


def cmd_ensure_secret(
    version: str,
    *,
    profile_dir: str | None,
    channel: str | None,
    headless: bool,
    timeout_ms: int,
    dry_run: bool,
) -> bool:
    """Open the Kaggle editor and attach WANDB_API_KEY if needed."""
    return _run_editor_action(
        version,
        "ensure-secret",
        profile_dir=profile_dir,
        channel=channel,
        headless=headless,
        timeout_ms=timeout_ms,
        dry_run=dry_run,
    )


def cmd_run_editor(
    version: str,
    *,
    profile_dir: str | None,
    channel: str | None,
    headless: bool,
    timeout_ms: int,
    dry_run: bool,
) -> bool:
    """Launch a secret-aware Kaggle editor run."""
    return _run_editor_action(
        version,
        "run-editor",
        profile_dir=profile_dir,
        channel=channel,
        headless=headless,
        timeout_ms=timeout_ms,
        dry_run=dry_run,
    )


def cmd_run(
    version: str,
    interval: int = 60,
    max_retries: int = 3,
    *,
    profile_dir: str | None,
    channel: str | None,
    headless: bool,
    timeout_ms: int,
    dry_run: bool,
) -> None:
    """Push notebook, launch via the Kaggle editor, and monitor with auto-fix."""
    print(f"=== Running {version} with secret-aware editor launch ===\n")
    if dry_run:
        print("Dry run: skipping Kaggle upload and browser launch.")
        cmd_run_editor(
            version,
            profile_dir=profile_dir,
            channel=channel,
            headless=headless,
            timeout_ms=timeout_ms,
            dry_run=True,
        )
        return
    if not cmd_push(version):
        print("ERROR: Failed to push notebook")
        sys.exit(1)

    if not cmd_run_editor(
        version,
        profile_dir=profile_dir,
        channel=channel,
        headless=headless,
        timeout_ms=timeout_ms,
        dry_run=dry_run,
    ):
        print("ERROR: Failed to launch the Kaggle editor workflow")
        sys.exit(1)

    print("\nStarting monitor...")
    print("-" * 50)
    monitor_script = SCRIPTS_DIR / "monitor_kaggle.py"
    result = subprocess.run(
        [
            str(WORKFLOW_PYTHON),
            str(monitor_script),
            version,
            "--interval",
            str(interval),
            "--max-retries",
            str(max_retries),
        ]
    )
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
    parser.add_argument(
        "command",
        choices=["preflight", "run", "push", "ensure-secret", "run-editor", "status", "pull", "list"],
        help="run=push+editor-launch+monitor, push=upload only",
    )
    parser.add_argument("version", nargs="?", help="Notebook version (e.g., vR.1)")
    parser.add_argument("--interval", type=int, default=60, help="Monitor check interval (default: 60s)")
    parser.add_argument("--max-retries", type=int, default=3, help="Max auto-fix retries (default: 3)")
    parser.add_argument("--profile-dir", default=None, help="Persistent browser profile for Kaggle editor auth")
    parser.add_argument("--channel", default=None, help="Browser channel for Playwright (default: msedge on Windows)")
    parser.add_argument("--headless", action="store_true", help="Run browser automation headlessly")
    parser.add_argument("--timeout-ms", type=int, default=120000, help="Browser automation timeout (default: 120000)")
    parser.add_argument("--dry-run", action="store_true", help="Print the planned browser command without launching it")
    args = parser.parse_args()

    if args.command == "list":
        cmd_list()
    elif args.version is None:
        parser.error(f"'{args.command}' requires a version argument")
    elif args.command == "preflight":
        cmd_preflight(args.version)
    elif args.command == "run":
        cmd_run(
            args.version,
            args.interval,
            args.max_retries,
            profile_dir=args.profile_dir,
            channel=args.channel,
            headless=args.headless,
            timeout_ms=args.timeout_ms,
            dry_run=args.dry_run,
        )
    elif args.command == "push":
        if not cmd_push(args.version):
            sys.exit(1)
    elif args.command == "ensure-secret":
        if not cmd_ensure_secret(
            args.version,
            profile_dir=args.profile_dir,
            channel=args.channel,
            headless=args.headless,
            timeout_ms=args.timeout_ms,
            dry_run=args.dry_run,
        ):
            sys.exit(1)
    elif args.command == "run-editor":
        if not cmd_run_editor(
            args.version,
            profile_dir=args.profile_dir,
            channel=args.channel,
            headless=args.headless,
            timeout_ms=args.timeout_ms,
            dry_run=args.dry_run,
        ):
            sys.exit(1)
    elif args.command == "status":
        cmd_status(args.version)
    elif args.command == "pull":
        cmd_pull(args.version)


if __name__ == "__main__":
    main()
