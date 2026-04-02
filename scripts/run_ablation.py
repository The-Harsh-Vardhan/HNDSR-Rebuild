"""Run bounded ablations for the HNDSR rebuild track."""

from __future__ import annotations

import argparse
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.utils import load_config, prepare_workspace_temp, repo_path


ABLATIONS = {
    "sr3_smoke": [
        ("mc32_steps10", {"model": {"model_channels": 32}, "diffusion": {"inference_steps": 10}}),
        ("mc32_steps20", {"model": {"model_channels": 32}, "diffusion": {"inference_steps": 20}}),
        ("mc64_steps10", {"model": {"model_channels": 64}, "diffusion": {"inference_steps": 10}}),
    ]
}


def deep_merge(base: dict, override: dict) -> dict:
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def write_variant_config(base_config: dict, study: str, name: str, override: dict) -> Path:
    variant = deep_merge(base_config, override)
    variant["project"]["tags"] = list(dict.fromkeys([*variant["project"].get("tags", []), "ablation", study]))
    target = repo_path(f"artifacts/ablations/{study}/{name}/config.yaml")
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(variant, handle, sort_keys=False)
    return target


def run_variant(config_path: Path, name: str) -> None:
    script_dir = Path(__file__).resolve().parent
    subprocess.run([sys.executable, str(script_dir / "train_baseline.py"), "--config", str(config_path), "--run-name", name], check=True)
    subprocess.run([sys.executable, str(script_dir / "evaluate_run.py"), "--config", str(config_path), "--run-name", name], check=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run bounded HNDSR ablations")
    parser.add_argument("--study", required=True, choices=sorted(ABLATIONS), help="Named ablation study")
    parser.add_argument("--base-config", required=True, help="Base YAML config to expand from")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base_config = load_config(args.base_config)
    prepare_workspace_temp(base_config["paths"]["artifact_root"])
    for name, override in ABLATIONS[args.study]:
        config_path = write_variant_config(base_config, args.study, name, override)
        run_variant(config_path, f"{args.study}-{name}")


if __name__ == "__main__":
    main()
