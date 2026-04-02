"""Contracts for Kaggle notebook and dataset metadata."""

from __future__ import annotations

import json
from pathlib import Path

from .utils import repo_path


KERNEL_METADATA_PATH = "notebooks/versions/kernel-metadata.json"
DATASET_METADATA_PATH = "kaggle/dataset-metadata.json"
CODE_DATASET_ID = "harshv777/hndsr-mini-project-code"


def load_json(path: str | Path) -> dict:
    resolved = repo_path(path)
    return json.loads(resolved.read_text(encoding="utf-8"))


def load_kernel_metadata() -> dict:
    return load_json(KERNEL_METADATA_PATH)


def load_dataset_metadata() -> dict:
    return load_json(DATASET_METADATA_PATH)


def validate_kernel_metadata(version: str, metadata: dict | None = None) -> list[str]:
    """Validate that kernel metadata matches the requested notebook version."""
    payload = metadata or load_kernel_metadata()
    failures: list[str] = []
    expected_code_file = f"{version}_HNDSR.ipynb"

    if payload.get("code_file") != expected_code_file:
        failures.append(f"kernel metadata code_file must be {expected_code_file}.")
    if "/" not in payload.get("id", ""):
        failures.append("kernel metadata id must include <username>/<slug>.")
    if not payload.get("title", "").startswith(version):
        failures.append(f"kernel metadata title must start with {version}.")
    if CODE_DATASET_ID not in payload.get("dataset_sources", []):
        failures.append(f"kernel metadata must include dataset source {CODE_DATASET_ID}.")
    if not payload.get("enable_gpu", False):
        failures.append("kernel metadata must keep GPU enabled.")
    return failures


def validate_dataset_metadata(metadata: dict | None = None) -> list[str]:
    """Validate the dataset packaging metadata used for Kaggle uploads."""
    payload = metadata or load_dataset_metadata()
    failures: list[str] = []
    if payload.get("id") != CODE_DATASET_ID:
        failures.append(f"dataset metadata id must be {CODE_DATASET_ID}.")
    if payload.get("title") != "HNDSR Mini Project Code":
        failures.append("dataset metadata title must stay aligned with the published Kaggle dataset.")
    licenses = payload.get("licenses", [])
    if not licenses or licenses[0].get("name") != "MIT":
        failures.append("dataset metadata must declare the MIT license.")
    return failures
