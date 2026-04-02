from pathlib import Path
from uuid import uuid4

import torch
from PIL import Image

from src.dataset import (
    SatellitePairDataset,
    SyntheticSatellitePairDataset,
    build_loaders,
)
from src.models import SR3Baseline
from src.tracker import NullTracker
from src import tracker as tracker_module
from src.utils import REPO_ROOT, get_device, load_config


def _write_fake_image(path: Path, color: tuple[int, int, int], size: tuple[int, int] = (96, 96)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", size, color=color)
    image.save(path)


def _fresh_dir(name: str) -> Path:
    base = Path("artifacts/test-fixtures")
    base.mkdir(parents=True, exist_ok=True)
    root = base / f"{name}-{uuid4().hex[:8]}"
    root.mkdir(parents=True, exist_ok=False)
    return root


def _paper_config(root: Path, dataset_name: str) -> dict:
    config = load_config("configs/base.yaml")
    config["dataset"] = {
        "family": "paper",
        "name": dataset_name,
        "pairing_mode": "synthetic_4x",
        "scale_factor": 4,
    }
    config["paths"]["datasets"][dataset_name]["root_dir"] = str(root)
    config["data"]["train_limit"] = None
    config["data"]["val_limit"] = None
    return config


def test_base_config_loads():
    config = load_config("configs/phase1_sr3_smoke.yaml")
    assert config["model"]["kind"] == "sr3"
    assert config["data"]["fixed_scale"] == 4
    assert config["dataset"]["name"] == "kaggle_4x"


def test_sr3_forward_loss_contract():
    model = SR3Baseline(model_channels=16, num_timesteps=32, beta_start=1.0e-4, beta_end=0.02)
    lr_upscaled = torch.randn(2, 3, 64, 64)
    hr = torch.randn(2, 3, 64, 64)
    loss, stats = model.training_step(lr_upscaled, hr)
    assert loss.ndim == 0
    assert "timesteps_mean" in stats


def test_null_tracker_accepts_logs():
    tracker = NullTracker(run_dir=".tmp/test-null-tracker")
    tracker.log_metrics({"loss": 1.0}, step=1)
    tracker.log_text("status", "ok")
    tracker.finish()


def test_repo_root_resolves_the_standalone_repo():
    assert (REPO_ROOT / "README.md").exists()
    assert (REPO_ROOT / "configs" / "base.yaml").exists()
    assert (REPO_ROOT / "scripts" / "kaggle_workflow.py").exists()


def test_synthetic_dataset_generates_deterministic_4x_pair():
    root = _fresh_dir("synthetic-ucmerced")
    _write_fake_image(root / "airport" / "sample_001.png", (200, 100, 50))
    dataset = SyntheticSatellitePairDataset(str(root), patch_size=64, training=False, scale_factor=4)
    sample_a = dataset[0]
    sample_b = dataset[0]
    assert sample_a["name"] == "airport__sample_001"
    assert sample_a["scale"] == 4
    assert tuple(sample_a["hr"].shape) == (3, 64, 64)
    assert tuple(sample_a["lr"].shape) == (3, 16, 16)
    assert torch.allclose(sample_a["hr"], sample_b["hr"])
    assert torch.allclose(sample_a["lr"], sample_b["lr"])


def test_paper_dataset_splits_are_stable_for_each_named_dataset():
    dataset_names = ["ucmerced", "aid", "rsscn7"]
    for dataset_name in dataset_names:
        root = _fresh_dir(f"split-{dataset_name}")
        for index in range(10):
            class_name = f"class_{index % 2}"
            _write_fake_image(root / class_name / f"sample_{index:03d}.png", (index * 10, 50, 100))
        config = _paper_config(root, dataset_name)
        bundle_a = build_loaders(config, seed=42)
        bundle_b = build_loaders(config, seed=42)
        names_a = [batch["name"][0] for batch in bundle_a.val_loader]
        names_b = [batch["name"][0] for batch in bundle_b.val_loader]
        assert bundle_a.dataset_name == dataset_name
        assert bundle_a.pairing_mode == "synthetic_4x"
        assert names_a == names_b


def test_kaggle_pairing_lane_preserves_traceable_names():
    root = _fresh_dir("kaggle-paired")
    hr_root = root / "kaggle" / "HR"
    lr_root = root / "kaggle" / "LR"
    _write_fake_image(hr_root / "tile_001.png", (220, 40, 40), size=(96, 96))
    _write_fake_image(lr_root / "tile_001.png", (200, 30, 30), size=(24, 24))
    _write_fake_image(hr_root / "tile_002.png", (120, 80, 40), size=(96, 96))
    _write_fake_image(lr_root / "tile_002.png", (110, 70, 30), size=(24, 24))
    config = load_config("configs/base.yaml")
    config["dataset"] = {
        "family": "kaggle",
        "name": "kaggle_4x",
        "pairing_mode": "paired",
        "scale_factor": 4,
    }
    config["paths"]["datasets"]["kaggle_4x"]["hr_dir"] = str(hr_root)
    config["paths"]["datasets"]["kaggle_4x"]["lr_dir"] = str(lr_root)
    config["data"]["val_split"] = 0.5
    config["data"]["train_limit"] = None
    config["data"]["val_limit"] = None
    bundle = build_loaders(config, seed=42)
    first_batch = next(iter(bundle.val_loader))
    assert first_batch["name"][0] in {"tile_001", "tile_002"}
    assert int(first_batch["scale"][0]) == 4


def test_kaggle_nested_mount_layout_is_resolved(monkeypatch):
    root = _fresh_dir("kaggle-nested-mount")
    kaggle_input = root / "input" / "4x-satellite-image-super-resolution"
    hr_root = kaggle_input / "HR_0.5m" / "HR_0.5m"
    lr_root = kaggle_input / "LR_2m" / "LR_2m"
    _write_fake_image(hr_root / "tile_001.tif", (220, 40, 40), size=(96, 96))
    _write_fake_image(lr_root / "tile_001.tif", (200, 30, 30), size=(24, 24))
    _write_fake_image(hr_root / "tile_002.tif", (120, 80, 40), size=(96, 96))
    _write_fake_image(lr_root / "tile_002.tif", (110, 70, 30), size=(24, 24))
    monkeypatch.setenv("HNDSR_KAGGLE_INPUT_ROOT", str(root / "input"))
    dataset = SatellitePairDataset(
        hr_dir="data/kaggle_4x/HR_0.5m",
        lr_dir="data/kaggle_4x/LR_2m",
        patch_size=64,
        training=False,
    )
    assert len(dataset) == 2
    sample = dataset[0]
    assert sample["name"] in {"tile_001", "tile_002"}
    assert sample["scale"] == 4


def test_get_device_falls_back_to_cpu_for_unsupported_cuda(monkeypatch):
    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
    monkeypatch.setattr(torch.cuda, "get_device_capability", lambda index=0: (6, 0))
    assert str(get_device()) == "cpu"


def test_tracker_requires_wandb_secret_when_enforced(monkeypatch):
    config = load_config("configs/phase1_sr3_vr1_kaggle.yaml")
    monkeypatch.setenv("HNDSR_REQUIRE_WANDB_AUTH", "1")
    monkeypatch.delenv("WANDB_API_KEY", raising=False)
    try:
        tracker_module.init_tracker(config, "test-run", ".tmp/test-tracker")
    except RuntimeError as exc:
        assert "WANDB_API_KEY" in str(exc)
    else:
        raise AssertionError("Expected authenticated tracking to reject a missing WANDB secret.")
