from pathlib import Path

from scripts.kaggle_workflow import build_editor_runner_command


def test_editor_runner_command_uses_playwright_wrapper():
    command = build_editor_runner_command(
        "vR.1",
        "run-editor",
        profile_dir=Path("artifacts/playwright/profile"),
        debug_dir=Path("artifacts/playwright/vR.1"),
        channel="msedge",
        headless=False,
        timeout_ms=120000,
        dry_run=True,
    )
    assert "--package" in command
    assert "playwright" in command
    assert "kaggle_editor_runner.mjs" in " ".join(command)
    assert "--kernel-id" in command
    assert "--secret-name" in command
    assert "--dry-run" in command
