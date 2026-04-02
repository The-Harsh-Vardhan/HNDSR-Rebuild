"""Version naming and file-layout helpers for the standalone research loop."""

from __future__ import annotations

from pathlib import Path
import re


VERSION_RE = re.compile(r"^vR(?:\.P)?\.\d+$")


def validate_version_label(version: str) -> None:
    if not VERSION_RE.match(version):
        raise ValueError(f"Unsupported notebook version label: {version}")


def notebook_stem(version: str) -> str:
    validate_version_label(version)
    return f"{version}_HNDSR"


def compact_version(version: str) -> str:
    validate_version_label(version)
    return version.lower().replace(".", "")


def kernel_version_slug(version: str) -> str:
    validate_version_label(version)
    return version.lower().replace(".", "-")


def default_contract_paths(version: str) -> dict[str, Path]:
    stem = notebook_stem(version)
    compact = compact_version(version)
    return {
        "notebook": Path(f"notebooks/versions/{stem}.ipynb"),
        "doc": Path(f"docs/notebooks/{stem}.md"),
        "review": Path(f"reports/reviews/{stem}.review.md"),
        "full_config": Path(f"configs/phase1_sr3_{compact}_kaggle.yaml"),
        "smoke_config": Path(f"configs/phase1_sr3_{compact}_smoke.yaml"),
        "control_config": Path(f"configs/phase0_bicubic_{compact}_kaggle_control.yaml"),
    }


def default_kernel_title(version: str) -> str:
    validate_version_label(version)
    return f"{version} HNDSR SR3 Baseline"


def default_kernel_slug(version: str) -> str:
    return f"{kernel_version_slug(version)}-hndsr-sr3-baseline"
