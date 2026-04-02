"""Version naming and file-layout helpers for the standalone research loop."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


VERSION_RE = re.compile(r"^vR(?:\.P)?\.\d+$")


@dataclass(frozen=True)
class VersionLane:
    """Version-specific config and Kaggle metadata naming."""

    config_prefix: str
    kernel_suffix: str
    title_suffix: str


VERSION_LANES = {
    "sr3": VersionLane(
        config_prefix="phase1_sr3",
        kernel_suffix="hndsr-sr3-baseline",
        title_suffix="HNDSR SR3 Baseline",
    ),
    "supervised": VersionLane(
        config_prefix="phase2_supervised",
        kernel_suffix="hndsr-supervised-baseline",
        title_suffix="HNDSR Supervised Baseline",
    ),
}

DEFAULT_VERSION_LANES = {
    "vR.1": "sr3",
    "vR.2": "supervised",
}


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


def lane_for_version(version: str) -> str:
    validate_version_label(version)
    return DEFAULT_VERSION_LANES.get(version, "sr3")


def default_contract_paths(version: str, lane: str | None = None) -> dict[str, Path]:
    stem = notebook_stem(version)
    compact = compact_version(version)
    selected_lane = VERSION_LANES[lane or lane_for_version(version)]
    return {
        "notebook": Path(f"notebooks/versions/{stem}.ipynb"),
        "doc": Path(f"docs/notebooks/{stem}.md"),
        "review": Path(f"reports/reviews/{stem}.review.md"),
        "full_config": Path(f"configs/{selected_lane.config_prefix}_{compact}_kaggle.yaml"),
        "smoke_config": Path(f"configs/{selected_lane.config_prefix}_{compact}_smoke.yaml"),
        "control_config": Path(f"configs/phase0_bicubic_{compact}_kaggle_control.yaml"),
    }


def default_kernel_title(version: str, lane: str | None = None) -> str:
    validate_version_label(version)
    selected_lane = VERSION_LANES[lane or lane_for_version(version)]
    return f"{version} {selected_lane.title_suffix}"


def default_kernel_slug(version: str, lane: str | None = None) -> str:
    selected_lane = VERSION_LANES[lane or lane_for_version(version)]
    return f"{kernel_version_slug(version)}-{selected_lane.kernel_suffix}"
