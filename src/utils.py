"""Utilities for the isolated HNDSR rebuild track."""

from __future__ import annotations

import json
import importlib.util
import os
import random
import sys
import tempfile
from copy import deepcopy
from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    import torch


def _is_relative_to(path: Path, other: Path) -> bool:
    try:
        path.relative_to(other)
        return True
    except ValueError:
        return False


def detect_repo_root() -> Path:
    """Resolve either the monorepo root or a standalone export root."""
    current = Path(__file__).resolve()
    for candidate in current.parents:
        track_root = candidate / "research_tracks" / "hndsr_rebuild"
        if (track_root / "src").exists() and _is_relative_to(current, track_root):
            return candidate
    for candidate in current.parents:
        if (candidate / "src").exists() and (candidate / "configs").exists() and (candidate / "scripts").exists():
            return candidate
    raise RuntimeError("Could not detect the HNDSR rebuild repo root.")


REPO_ROOT = detect_repo_root()


def repo_path(value: str | Path) -> Path:
    """Resolve a repo-relative path without guessing from cwd."""
    candidate = Path(value)
    if candidate.is_absolute():
        return candidate
    return REPO_ROOT / candidate


def ensure_dir(path: str | Path) -> Path:
    """Create a directory if it does not already exist."""
    target = repo_path(path)
    target.mkdir(parents=True, exist_ok=True)
    return target


def prepare_workspace_temp(root: str | Path) -> Path:
    """Force temporary files into the workspace to avoid broken system temp permissions."""
    temp_root = ensure_dir(Path(root) / ".tmp" / "temp")
    os.environ["TMP"] = str(temp_root)
    os.environ["TEMP"] = str(temp_root)
    os.environ["TMPDIR"] = str(temp_root)
    tempfile.tempdir = str(temp_root)
    return temp_root


def resolve_python_executable() -> Path:
    """Prefer a nearby repo virtualenv for workflow helpers, then fall back to the active interpreter."""
    override = os.environ.get("HNDSR_PYTHON")
    if override:
        return Path(override)
    for candidate_root in (REPO_ROOT, *REPO_ROOT.parents):
        windows_python = candidate_root / ".venv" / "Scripts" / "python.exe"
        if windows_python.exists():
            return windows_python
        posix_python = candidate_root / ".venv" / "bin" / "python"
        if posix_python.exists():
            return posix_python
    return Path(sys.executable)


def resolve_kaggle_cli() -> tuple[list[str], dict[str, str]]:
    """Resolve a Kaggle CLI invocation that survives Windows Store Python shims."""
    if importlib.util.find_spec("kaggle.cli") is not None:
        return [sys.executable, "-m", "kaggle.cli"], os.environ.copy()

    store_site_packages = _find_store_kaggle_site_packages()
    if store_site_packages is not None:
        env = os.environ.copy()
        existing = env.get("PYTHONPATH")
        env["PYTHONPATH"] = (
            f"{store_site_packages}{os.pathsep}{existing}" if existing else str(store_site_packages)
        )
        return [sys.executable, "-m", "kaggle.cli"], env

    return ["kaggle"], os.environ.copy()


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config(path: str | Path) -> dict[str, Any]:
    """Load a YAML config with optional `inherits` support."""
    yaml = _require_yaml()
    resolved = repo_path(path)
    with resolved.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}
    parent = config.pop("inherits", None)
    if not parent:
        return config
    base = load_config(parent)
    return _deep_merge(base, config)


def write_json(path: str | Path, payload: dict[str, Any]) -> Path:
    """Persist a JSON payload with stable formatting."""
    resolved = repo_path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    with resolved.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
    return resolved


def set_seed(seed: int) -> None:
    """Set deterministic seeds across Python, NumPy, and PyTorch."""
    np = _require_numpy()
    torch = _require_torch()
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True


def get_device(explicit: str | None = None) -> torch.device:
    """Pick a device conservatively for reproducible experiments."""
    torch = _require_torch()
    if explicit:
        return torch.device(explicit)
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def _require_torch() -> Any:
    try:
        import torch
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "PyTorch is required for training or evaluation commands. "
            "Use the project ML environment before running model code."
        ) from exc
    return torch


def _require_numpy() -> Any:
    try:
        import numpy as np
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "NumPy is required for training or evaluation commands. "
            "Use the project ML environment before running model code."
        ) from exc
    return np


def _require_yaml() -> Any:
    try:
        import yaml
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "PyYAML is required for config-driven commands. "
            "Use the project ML environment or set HNDSR_PYTHON to a suitable interpreter."
        ) from exc
    return yaml


def _find_store_kaggle_site_packages() -> Path | None:
    packages_root = Path.home() / "AppData" / "Local" / "Packages"
    if not packages_root.exists():
        return None
    for candidate in sorted(packages_root.glob("PythonSoftwareFoundation.Python.*")):
        local_packages = candidate / "LocalCache" / "local-packages"
        for python_dir in sorted(local_packages.glob("Python*")):
            site_packages = python_dir / "site-packages"
            if (site_packages / "kaggle").exists():
                return site_packages
    return None


def flatten_config(config: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    """Flatten a nested config for tracker logging."""
    flat: dict[str, Any] = {}
    for key, value in config.items():
        scoped = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            flat.update(flatten_config(value, scoped))
        else:
            flat[scoped] = value
    return flat


def describe_run_dirs(config: dict[str, Any], run_name: str) -> dict[str, Path]:
    """Compute the tracked output directories for a run."""
    artifact_root = ensure_dir(config["paths"]["artifact_root"])
    run_root = artifact_root / run_name
    return {
        "artifact_root": artifact_root,
        "run_root": ensure_dir(run_root),
        "checkpoints": ensure_dir(run_root / "checkpoints"),
        "metrics": ensure_dir(run_root / "metrics"),
        "samples": ensure_dir(run_root / "samples"),
        "tracker": ensure_dir(run_root / "tracker"),
    }
