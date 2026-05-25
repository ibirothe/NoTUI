from __future__ import annotations

from pathlib import Path

import pytest

from notui import __version__
from notui.cli import build_parser, doctor
from notui.config import AppConfig, Theme, UIConfig


def test_version_uses_brand_name(capsys: pytest.CaptureFixture[str]) -> None:
    parser = build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(["--version"])

    assert capsys.readouterr().out.strip() == f"NoTUI {__version__}"


def test_doctor_reports_notui_paths_and_brand(capsys: pytest.CaptureFixture[str], tmp_path) -> None:
    config = AppConfig(
        database_path=None,
        theme=Theme(),
        theme_is_custom=False,
        ui=UIConfig(),
        config_path=tmp_path / "config" / "notui" / "config.toml",
        state_dir=tmp_path / "state" / "notui",
    )
    db_path = Path(tmp_path / "data" / "notui" / "notui.sqlite")

    assert doctor(config, db_path) == 0

    output = capsys.readouterr().out
    assert f"NoTUI version: {__version__}" in output
    assert f"Database path: {db_path}" in output
    assert "background: #0b0b0b" in output
