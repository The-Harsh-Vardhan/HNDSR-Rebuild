#!/usr/bin/env python3
"""Scaffold the next immutable notebook version from the last reviewed one."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.utils import REPO_ROOT
from src.versioning import default_contract_paths, default_kernel_slug, default_kernel_title, lane_for_version, notebook_stem


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scaffold the next notebook version")
    parser.add_argument("--from-version", required=True, help="Existing version, for example vR.1")
    parser.add_argument("--to-version", required=True, help="New version, for example vR.2")
    parser.add_argument(
        "--from-lane",
        default=None,
        help="Optional source lane override, for example sr3 or supervised",
    )
    parser.add_argument(
        "--to-lane",
        default=None,
        help="Optional target lane override, for example sr3 or supervised",
    )
    parser.add_argument(
        "--activate-kaggle",
        action="store_true",
        help="Update notebooks/versions/kernel-metadata.json to point at the new version",
    )
    return parser.parse_args()


def ensure_missing(path: Path) -> None:
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite existing file: {path}")


def replace_text(path: Path, replacements: list[tuple[str, str]]) -> None:
    text = path.read_text(encoding="utf-8")
    for old, new in replacements:
        text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")


def main() -> None:
    args = parse_args()
    from_lane = args.from_lane or lane_for_version(args.from_version)
    to_lane = args.to_lane or lane_for_version(args.to_version)
    source = default_contract_paths(args.from_version, lane=from_lane)
    target = default_contract_paths(args.to_version, lane=to_lane)

    for path in source.values():
        resolved = REPO_ROOT / path
        if not resolved.exists():
            raise FileNotFoundError(f"Missing source contract file: {resolved}")

    for path in target.values():
        ensure_missing(REPO_ROOT / path)

    ordered_replacements = [
        (str(source["full_config"]).replace("\\", "/"), str(target["full_config"]).replace("\\", "/")),
        (str(source["smoke_config"]).replace("\\", "/"), str(target["smoke_config"]).replace("\\", "/")),
        (str(source["control_config"]).replace("\\", "/"), str(target["control_config"]).replace("\\", "/")),
        (notebook_stem(args.from_version), notebook_stem(args.to_version)),
        (args.from_version, args.to_version),
    ]

    for key, source_path in source.items():
        target_path = target[key]
        shutil.copy2(REPO_ROOT / source_path, REPO_ROOT / target_path)
        replace_text(REPO_ROOT / target_path, ordered_replacements)
        print(f"Created {target_path}")

    if args.activate_kaggle:
        metadata_path = REPO_ROOT / "notebooks/versions/kernel-metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        owner = metadata["id"].split("/", 1)[0]
        metadata["id"] = f"{owner}/{default_kernel_slug(args.to_version, lane=to_lane)}"
        metadata["title"] = default_kernel_title(args.to_version, lane=to_lane)
        metadata["code_file"] = f"{notebook_stem(args.to_version)}.ipynb"
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        print("Updated notebooks/versions/kernel-metadata.json")


if __name__ == "__main__":
    main()
