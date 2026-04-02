"""Validation helpers for immutable versioned Kaggle notebooks."""

from __future__ import annotations

import json
from pathlib import Path

from .tracker import init_tracker
from .utils import load_config, prepare_workspace_temp, repo_path


COMMON_NOTEBOOK_SECTIONS = (
    "## Runtime Compatibility Check",
    "## Post-Restart GPU Sanity Check",
    "## Experiment Registry",
    "## Paper Lineage and Hypothesis",
    "## Dataset and Config Contract",
    "## Weights & Biases Setup",
    "## Training Execution",
    "## Evaluation and Export",
    "## Results Dashboard",
    "## Troubleshooting and Known Failure Modes",
    "## Changelog",
    "## Next Step Gate",
)

COMMON_NOTEBOOK_COMMANDS = (
    "scripts/validate_notebook_version.py",
    "scripts/train_baseline.py",
    "scripts/evaluate_run.py",
)

COMMON_DOC_SECTIONS = (
    "## Objective",
    "## Kaggle Run Guide",
    "## Config Contract",
    "## Expected Artifacts",
    "## Handoff Back For Review",
)

COMMON_REVIEW_SECTIONS = (
    "## Status",
    "## Run Intake",
    "## Audit Checklist",
    "## Findings",
    "## Promotion Decision",
)


def _load_text(path: str | Path) -> str:
    resolved = repo_path(path)
    return resolved.read_text(encoding="utf-8")


def _load_notebook_text(path: str | Path) -> str:
    resolved = repo_path(path)
    notebook = json.loads(resolved.read_text(encoding="utf-8"))
    return "\n".join("".join(cell.get("source", [])) for cell in notebook.get("cells", []))


def _missing_fragments(text: str, fragments: tuple[str, ...], label: str) -> list[str]:
    failures: list[str] = []
    for fragment in fragments:
        if fragment not in text:
            failures.append(f"{label} is missing fragment: {fragment}")
    return failures


def validate_versioned_notebook(
    notebook_path: str | Path,
    doc_path: str | Path,
    review_path: str | Path,
    full_config_path: str | Path,
    smoke_config_path: str | Path,
    control_config_path: str | Path,
    version: str,
) -> list[str]:
    """Validate the first immutable notebook contract before Kaggle handoff."""
    failures: list[str] = []
    notebook_text = _load_notebook_text(notebook_path)
    doc_text = _load_text(doc_path)
    review_text = _load_text(review_path)
    expected_commands = (
        *COMMON_NOTEBOOK_COMMANDS,
        Path(full_config_path).name,
        Path(smoke_config_path).name,
        Path(control_config_path).name,
        "HNDSR_REQUIRE_WANDB_AUTH",
    )
    failures.extend(_missing_fragments(notebook_text, (f"# {version} HNDSR", *COMMON_NOTEBOOK_SECTIONS), "Notebook"))
    failures.extend(_missing_fragments(notebook_text, expected_commands, "Notebook"))
    failures.extend(_missing_fragments(doc_text, (f"# {version} HNDSR", *COMMON_DOC_SECTIONS), "Doc"))
    failures.extend(_missing_fragments(review_text, (f"# {version} HNDSR Review", *COMMON_REVIEW_SECTIONS), "Review"))

    for config_path in (full_config_path, smoke_config_path, control_config_path):
        config = load_config(config_path)
        if config["dataset"]["name"] != "kaggle_4x":
            failures.append(f"{config_path} must target kaggle_4x for {version}.")
        if config["dataset"]["pairing_mode"] != "paired":
            failures.append(f"{config_path} must use paired LR/HR loading for {version}.")
        if config["dataset"]["scale_factor"] != 4:
            failures.append(f"{config_path} must keep a fixed 4x scale.")
        if not config["training"].get("checkpoint_name"):
            failures.append(f"{config_path} must declare checkpoint_name.")
        if config["tracking"].get("mode") not in {"offline", "online", "disabled"}:
            failures.append(f"{config_path} has unsupported tracking.mode.")

    full_config = load_config(full_config_path)
    prepare_workspace_temp(full_config["paths"]["artifact_root"])
    tracker_dir = repo_path(".tmp/notebook-readiness/tracker")
    tracker = init_tracker(full_config, f"{version}-readiness-check", tracker_dir)
    tracker.log_metrics({"readiness_contract": 1.0}, step=1)
    tracker.log_text("version", version)
    tracker.finish()

    try:
        from . import tracker as _tracker  # noqa: F401
        from . import utils as _utils  # noqa: F401
    except Exception as exc:
        failures.append(f"Core rebuild-track imports failed: {exc}")

    return failures
