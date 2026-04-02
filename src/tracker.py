"""Tracking helpers with W&B fallback."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .utils import flatten_config, write_json


class NullTracker:
    """No-op tracker that still writes local run metadata."""

    def __init__(self, run_dir: str | Path) -> None:
        self.run_dir = Path(run_dir)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.records: list[dict[str, Any]] = []

    def log_metrics(self, metrics: dict[str, Any], step: int | None = None) -> None:
        payload = {"type": "metrics", "step": step, "values": metrics}
        self.records.append(payload)

    def log_text(self, name: str, text: str) -> None:
        payload = {"type": "text", "name": name, "value": text}
        self.records.append(payload)

    def log_image(self, name: str, path: str | Path) -> None:
        payload = {"type": "image", "name": name, "path": str(path)}
        self.records.append(payload)

    def finish(self) -> None:
        write_json(self.run_dir / "tracker_records.json", {"records": self.records})


class WandbTracker(NullTracker):
    """W&B-backed tracker with the same local fallback records."""

    def __init__(self, run_dir: str | Path, run: Any) -> None:
        super().__init__(run_dir)
        self.run = run
        self._wandb = __import__("wandb")

    def log_metrics(self, metrics: dict[str, Any], step: int | None = None) -> None:
        super().log_metrics(metrics, step)
        payload = dict(metrics)
        if step is not None:
            self.run.log(payload, step=step)
        else:
            self.run.log(payload)

    def log_text(self, name: str, text: str) -> None:
        super().log_text(name, text)
        self.run.summary[name] = text

    def log_image(self, name: str, path: str | Path) -> None:
        super().log_image(name, path)
        self.run.log({name: self._wandb.Image(str(path))})

    def finish(self) -> None:
        super().finish()
        self.run.finish()


def init_tracker(config: dict[str, Any], run_name: str, run_dir: str | Path) -> NullTracker:
    """Initialize W&B if possible, otherwise return a local no-op tracker."""
    tracking = config["tracking"]
    if not tracking.get("enabled", True):
        return NullTracker(run_dir)
    try:
        import wandb
    except Exception:
        return NullTracker(run_dir)
    try:
        run = wandb.init(
            project=tracking["project"],
            entity=tracking.get("entity"),
            group=config["project"]["group"],
            tags=config["project"].get("tags", []),
            notes=tracking.get("notes"),
            name=run_name,
            config=flatten_config(config),
            mode=tracking.get("mode", "offline"),
            reinit=True,
            dir=str(run_dir),
        )
    except Exception:
        return NullTracker(run_dir)
    return WandbTracker(run_dir, run)
