from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from notui import script_runner


def test_default_shell_uses_shell_environment(monkeypatch) -> None:
    monkeypatch.setenv("SHELL", "/bin/zsh")

    assert script_runner.default_shell() == "/bin/zsh"


def test_default_shell_falls_back_to_available_shell(monkeypatch) -> None:
    monkeypatch.delenv("SHELL", raising=False)
    monkeypatch.setattr(script_runner.shutil, "which", lambda name: f"/usr/bin/{name}")

    assert script_runner.default_shell() == "/usr/bin/bash"


def test_run_note_script_uses_temp_script_without_shell_true(monkeypatch) -> None:
    script_paths: list[Path] = []

    def fake_run(args: list[str], check: bool) -> SimpleNamespace:
        script_path = Path(args[1])
        script_paths.append(script_path)

        assert args[0] == "/bin/sh"
        assert check is False
        assert script_path.exists()
        assert script_path.read_text(encoding="utf-8") == "echo hello"
        assert script_path.stat().st_mode & 0o777 == 0o700

        return SimpleNamespace(returncode=3)

    monkeypatch.setattr(script_runner.subprocess, "run", fake_run)

    assert script_runner.run_note_script("echo hello", shell="/bin/sh") == 3
    assert len(script_paths) == 1
    assert not script_paths[0].exists()
