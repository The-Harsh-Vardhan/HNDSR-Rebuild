"""Validate the immutable contract for a versioned Kaggle notebook."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.notebook_contract import validate_versioned_notebook


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a versioned HNDSR Kaggle notebook")
    parser.add_argument("--version", required=True, help="Notebook version label, for example vR.1")
    parser.add_argument("--notebook", required=True, help="Path to the versioned notebook")
    parser.add_argument("--doc", required=True, help="Path to the paired notebook markdown doc")
    parser.add_argument("--review", required=True, help="Path to the paired review markdown doc")
    parser.add_argument("--config", required=True, help="Path to the primary training config")
    parser.add_argument("--smoke-config", required=True, help="Path to the smoke training config")
    parser.add_argument("--control-config", required=True, help="Path to the bicubic control config")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    failures = validate_versioned_notebook(
        notebook_path=args.notebook,
        doc_path=args.doc,
        review_path=args.review,
        full_config_path=args.config,
        smoke_config_path=args.smoke_config,
        control_config_path=args.control_config,
        version=args.version,
    )
    if failures:
        for failure in failures:
            print(f"[FAIL] {failure}")
        raise SystemExit(1)
    print(f"{args.version} notebook contract passed.")


if __name__ == "__main__":
    main()
