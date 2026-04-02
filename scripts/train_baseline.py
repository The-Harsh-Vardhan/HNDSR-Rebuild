"""Train an isolated baseline for the HNDSR rebuild track."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import torch
from torch.nn.utils import clip_grad_norm_
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.dataset import build_loaders
from src.metrics import bicubic_upscale, calculate_psnr
from src.models import SR3Baseline
from src.tracker import init_tracker
from src.utils import describe_run_dirs, get_device, load_config, prepare_workspace_temp, set_seed, write_json


def build_model(config: dict, device: torch.device) -> SR3Baseline:
    """Instantiate the selected trainable baseline."""
    if config["model"]["kind"] != "sr3":
        raise ValueError("train_baseline.py currently supports only the sr3 baseline.")
    model = SR3Baseline(
        model_channels=config["model"]["model_channels"],
        num_timesteps=config["diffusion"]["num_timesteps"],
        beta_start=config["diffusion"]["beta_start"],
        beta_end=config["diffusion"]["beta_end"],
    )
    return model.to(device)


def validate(model: SR3Baseline, val_loader, config: dict, device: torch.device) -> dict[str, float]:
    """Run a bounded validation pass with one quick sampling check."""
    model.eval()
    losses: list[float] = []
    psnr_values: list[float] = []
    max_batches = config["training"].get("max_val_batches")
    inference_steps = max(2, min(config["diffusion"]["inference_steps"], 4))
    with torch.no_grad():
        for batch_idx, batch in enumerate(val_loader):
            if max_batches is not None and batch_idx >= max_batches:
                break
            hr = batch["hr"].to(device)
            scale = int(batch["scale"][0])
            lr_upscaled = bicubic_upscale(batch["lr"].to(device), scale)
            loss, _ = model.training_step(lr_upscaled, hr)
            sample = model.sample(lr_upscaled, inference_steps=inference_steps)
            losses.append(float(loss.item()))
            psnr_values.append(calculate_psnr(sample, hr))
    return {
        "val_loss": float(sum(losses) / max(len(losses), 1)),
        "val_psnr": float(sum(psnr_values) / max(len(psnr_values), 1)),
    }


def train(config: dict, run_name: str, device: torch.device) -> dict[str, object]:
    """Train the selected baseline and persist the best checkpoint."""
    dirs = describe_run_dirs(config, run_name)
    tracker = init_tracker(config, run_name, dirs["tracker"])
    bundle = build_loaders(config, seed=config["seed"])
    model = build_model(config, device)
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=config["training"]["lr"],
        weight_decay=config["training"]["weight_decay"],
    )
    best_val_loss = float("inf")
    best_checkpoint = dirs["checkpoints"] / config["training"]["checkpoint_name"]
    history: list[dict[str, float]] = []
    for epoch in range(config["training"]["epochs"]):
        model.train()
        train_losses: list[float] = []
        progress = tqdm(bundle.train_loader, desc=f"SR3 epoch {epoch + 1}", leave=False)
        for batch_idx, batch in enumerate(progress):
            if batch_idx >= config["training"]["max_train_batches"]:
                break
            hr = batch["hr"].to(device)
            scale = int(batch["scale"][0])
            lr_upscaled = bicubic_upscale(batch["lr"].to(device), scale)
            optimizer.zero_grad(set_to_none=True)
            loss, stats = model.training_step(lr_upscaled, hr)
            loss.backward()
            clip_grad_norm_(model.parameters(), config["training"]["grad_clip"])
            optimizer.step()
            train_losses.append(float(loss.item()))
            progress.set_postfix({"loss": f"{loss.item():.4f}", "t": f"{stats['timesteps_mean']:.1f}"})
        validation = validate(model, bundle.val_loader, config, device)
        epoch_metrics = {
            "epoch": epoch + 1,
            "train_loss": float(sum(train_losses) / max(len(train_losses), 1)),
            **validation,
        }
        history.append(epoch_metrics)
        tracker.log_metrics(epoch_metrics, step=epoch + 1)
        if epoch_metrics["val_loss"] < best_val_loss:
            best_val_loss = epoch_metrics["val_loss"]
            torch.save({"model": model.state_dict(), "config": config}, best_checkpoint)
    summary = {
        "run_name": run_name,
        "model_kind": config["model"]["kind"],
        "dataset_family": config["dataset"]["family"],
        "dataset_name": bundle.dataset_name,
        "pairing_mode": bundle.pairing_mode,
        "device": str(device),
        "train_size": bundle.train_size,
        "val_size": bundle.val_size,
        "best_checkpoint": str(best_checkpoint),
        "best_val_loss": best_val_loss,
        "history": history,
    }
    write_json(dirs["metrics"] / "train_summary.json", summary)
    tracker.log_text("best_checkpoint", str(best_checkpoint))
    tracker.finish()
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train isolated HNDSR research baseline")
    parser.add_argument("--config", required=True, help="Path to the YAML config file")
    parser.add_argument("--run-name", default=None, help="Optional explicit run name")
    parser.add_argument("--device", default=None, help="Optional torch device override")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    prepare_workspace_temp(config["paths"]["artifact_root"])
    set_seed(config["seed"])
    run_name = args.run_name or f"{config['project']['group']}-{time.strftime('%Y%m%d-%H%M%S')}"
    device = get_device(args.device)
    if config["model"]["kind"] == "bicubic":
        raise ValueError("Use evaluate_run.py for the bicubic bootstrap baseline.")
    summary = train(config, run_name, device)
    print(f"Saved best checkpoint to {summary['best_checkpoint']}")


if __name__ == "__main__":
    main()
