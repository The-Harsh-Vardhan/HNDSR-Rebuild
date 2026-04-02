#!/usr/bin/env python3
"""Kaggle notebook monitor with auto-fix and retry capabilities.

Usage:
    python monitor_kaggle.py vR.1              # Monitor until complete
    python monitor_kaggle.py vR.1 --no-auto    # Monitor only, no auto-fix
    python monitor_kaggle.py vR.1 --max-retries 3  # Limit retries
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.kaggle_contract import load_kernel_metadata, validate_kernel_metadata

REPO_ROOT = Path(__file__).resolve().parents[2].parent
NOTEBOOKS_DIR = REPO_ROOT / "research_tracks" / "hndsr_rebuild" / "notebooks" / "versions"
RESULTS_DIR = REPO_ROOT / "research_tracks" / "hndsr_rebuild" / "artifacts" / "kaggle_outputs"

# Known error patterns and their fixes
ERROR_FIXES = {
    r"AssertionError: Expected rebuild track under repo root": {
        "description": "Dataset not properly attached or outdated",
        "action": "update_dataset",
    },
    r"ModuleNotFoundError: No module named": {
        "description": "Missing Python module",
        "action": "add_pip_install",
    },
    r"FileNotFoundError.*config.*yaml": {
        "description": "Config file not found - dataset may be outdated",
        "action": "update_dataset",
    },
    r"CUDA out of memory": {
        "description": "GPU memory exceeded - reduce batch size",
        "action": "reduce_batch_size",
    },
    r"KeyError:": {
        "description": "Missing key in config or data",
        "action": "manual_fix_required",
    },
}


def log(msg: str) -> None:
    """Print timestamped log message."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}")


def run_cmd(
    args: list[str],
    check: bool = True,
    capture: bool = False,
    **kwargs,
) -> subprocess.CompletedProcess:
    """Run a command and optionally capture output."""
    if capture:
        return subprocess.run(args, check=check, capture_output=True, text=True, **kwargs)
    return subprocess.run(args, check=check, **kwargs)


def get_kernel_id(version: str) -> str:
    """Get kernel ID from metadata."""
    meta = load_kernel_metadata()
    failures = validate_kernel_metadata(version, meta)
    if failures:
        raise ValueError("\n".join(failures))
    kernel_id = meta.get("id", "")
    if not kernel_id:
        raise ValueError("No kernel ID in metadata")
    return kernel_id


def get_status(kernel_id: str) -> str:
    """Get current kernel status."""
    result = run_cmd(["kaggle", "kernels", "status", kernel_id], capture=True, check=False)
    output = result.stdout + result.stderr

    if "RUNNING" in output:
        return "running"
    elif "COMPLETE" in output:
        return "complete"
    elif "ERROR" in output:
        return "error"
    elif "QUEUED" in output:
        return "queued"
    elif "CANCELLED" in output:
        return "cancelled"
    else:
        return "unknown"


def pull_logs(kernel_id: str, version: str) -> Path | None:
    """Pull kernel output and logs."""
    output_dir = RESULTS_DIR / version
    output_dir.mkdir(parents=True, exist_ok=True)

    run_cmd(["kaggle", "kernels", "output", kernel_id, "-p", str(output_dir)], check=False)

    # Find the log file
    log_files = list(output_dir.glob("*.log"))
    if log_files:
        return log_files[0]
    return None


def parse_error(log_path: Path) -> dict | None:
    """Parse error from log file and identify fix."""
    if not log_path or not log_path.exists():
        return None

    content = log_path.read_text(encoding="utf-8", errors="ignore")

    # Parse JSON log format
    error_lines = []
    for line in content.split("\n"):
        try:
            entry = json.loads(line.strip().rstrip(","))
            if entry.get("stream_name") == "stderr":
                error_lines.append(entry.get("data", ""))
        except json.JSONDecodeError:
            continue

    error_text = "".join(error_lines)

    # Match against known patterns
    for pattern, fix_info in ERROR_FIXES.items():
        if re.search(pattern, error_text):
            return {
                "pattern": pattern,
                "description": fix_info["description"],
                "action": fix_info["action"],
                "error_text": error_text[-2000:],  # Last 2000 chars
            }

    # Unknown error
    if "Error" in error_text or "Exception" in error_text:
        return {
            "pattern": "unknown",
            "description": "Unknown error",
            "action": "manual_fix_required",
            "error_text": error_text[-2000:],
        }

    return None


def apply_fix(error_info: dict, version: str) -> bool:
    """Apply automatic fix based on error type. Returns True if fix was applied."""
    action = error_info.get("action")

    if action == "update_dataset":
        log("Fix: Updating dataset...")
        log("  Creating new repo zip...")
        run_cmd([
            "git", "archive",
            "--format=zip",
            "--output", str(REPO_ROOT / "hndsr-repo.zip"),
            "--prefix=Mini Project/",
            "HEAD"
        ], cwd=REPO_ROOT)
        log("  ⚠️  Manual step required: Upload hndsr-repo.zip as new dataset version on Kaggle")
        log("  URL: https://www.kaggle.com/datasets/harshv777/hndsr-mini-project-code")

        # Wait for user confirmation
        input("  Press Enter after uploading the dataset...")
        return True

    elif action == "add_pip_install":
        # Extract module name from error
        match = re.search(r"No module named ['\"]?(\w+)", error_info.get("error_text", ""))
        if match:
            module = match.group(1)
            log(f"Fix: Need to add pip install for '{module}'")
            log("  ⚠️  Manual step: Add '!pip install {module}' to notebook setup cell")
        return False

    elif action == "reduce_batch_size":
        log("Fix: CUDA OOM - need to reduce batch size in config")
        log("  ⚠️  Manual step: Reduce batch_size in the config YAML")
        return False

    elif action == "manual_fix_required":
        log("⚠️  Manual fix required. Error details:")
        log("-" * 60)
        print(error_info.get("error_text", "No details available")[-1500:])
        log("-" * 60)
        return False

    return False


def push_notebook(version: str) -> bool:
    """Push notebook to Kaggle."""
    failures = validate_kernel_metadata(version, load_kernel_metadata())
    if failures:
        for failure in failures:
            log(f"Metadata error: {failure}")
        return False
    log("Pushing notebook to Kaggle...")
    result = run_cmd(
        ["kaggle", "kernels", "push", "-p", str(NOTEBOOKS_DIR)],
        check=False,
        capture=True
    )
    if result.returncode == 0:
        log("✓ Notebook pushed successfully")
        return True
    else:
        log(f"✗ Push failed: {result.stderr}")
        return False


def monitor_loop(
    version: str,
    interval: int = 60,
    max_retries: int = 3,
    auto_fix: bool = True,
) -> bool:
    """Main monitoring loop. Returns True if notebook completed successfully."""

    kernel_id = get_kernel_id(version)
    log(f"Monitoring kernel: {kernel_id}")
    log(f"Check interval: {interval}s | Max retries: {max_retries} | Auto-fix: {auto_fix}")
    log("-" * 60)

    retry_count = 0

    while True:
        status = get_status(kernel_id)
        log(f"Status: {status.upper()}")

        if status == "complete":
            log("✓ Notebook completed successfully!")
            log(f"Pull results with: python kaggle_workflow.py pull {version}")
            return True

        elif status == "error":
            log("✗ Notebook failed with error")

            # Pull and parse error
            log_path = pull_logs(kernel_id, version)
            error_info = parse_error(log_path)

            if error_info:
                log(f"Detected: {error_info['description']}")

                if auto_fix and retry_count < max_retries:
                    retry_count += 1
                    log(f"Attempting fix (retry {retry_count}/{max_retries})...")

                    if apply_fix(error_info, version):
                        if push_notebook(version):
                            log(f"Waiting {interval}s before checking status...")
                            time.sleep(interval)
                            continue
                    else:
                        log("Auto-fix not available for this error")
                        return False
                else:
                    if retry_count >= max_retries:
                        log(f"Max retries ({max_retries}) reached")
                    return False
            else:
                log("Could not parse error from logs")
                if log_path:
                    log(f"Check logs at: {log_path}")
                return False

        elif status == "cancelled":
            log("Notebook was cancelled")
            return False

        elif status in ("running", "queued"):
            # Still running, wait and check again
            pass

        else:
            log(f"Unknown status: {status}")

        time.sleep(interval)


def main() -> None:
    parser = argparse.ArgumentParser(description="Monitor Kaggle notebook with auto-fix")
    parser.add_argument("version", help="Notebook version (e.g., vR.1)")
    parser.add_argument("--interval", type=int, default=60, help="Check interval in seconds (default: 60)")
    parser.add_argument("--max-retries", type=int, default=3, help="Max auto-fix retries (default: 3)")
    parser.add_argument("--no-auto", action="store_true", help="Disable auto-fix")
    parser.add_argument("--once", action="store_true", help="Check once and exit")
    args = parser.parse_args()

    log(f"Starting monitor for {args.version}")

    if args.once:
        kernel_id = get_kernel_id(args.version)
        status = get_status(kernel_id)
        log(f"Status: {status.upper()}")
        sys.exit(0 if status == "complete" else 1)

    try:
        success = monitor_loop(
            version=args.version,
            interval=args.interval,
            max_retries=args.max_retries,
            auto_fix=not args.no_auto,
        )
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        log("\nMonitoring stopped by user")
        sys.exit(1)


if __name__ == "__main__":
    main()
