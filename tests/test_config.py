from __future__ import annotations

import pytest

from notui.config import (
    THEME_KEYS,
    Theme,
    default_db_path,
    load_config,
    load_saved_theme_name,
    save_theme_name,
    theme_state_path,
)
from notui.exceptions import ConfigError
from notui.tui.theme import BUILTIN_THEMES, theme_cycle


def test_theme_accepts_exact_four_colors() -> None:
    theme = Theme.from_mapping(
        {
            "background": "#000000",
            "panel_background": "#111111",
            "text": "#eeeeee",
            "secondary_text": "#888888",
        }
    )
    assert theme.text == "#eeeeee"


def test_theme_rejects_extra_colors() -> None:
    with pytest.raises(ConfigError):
        Theme.from_mapping(
            {
                "background": "#000000",
                "panel_background": "#111111",
                "text": "#eeeeee",
                "secondary_text": "#888888",
                "accent": "#ff0000",
            }
        )


def test_theme_rejects_invalid_hex() -> None:
    with pytest.raises(ConfigError):
        Theme.from_mapping(
            {
                "background": "black",
                "panel_background": "#111111",
                "text": "#eeeeee",
                "secondary_text": "#888888",
            }
        )


def test_default_paths_use_notui(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))

    config = load_config()

    assert config.config_path == tmp_path / "config" / "notui" / "config.toml"
    assert default_db_path() == tmp_path / "data" / "notui" / "notui.sqlite"
    assert config.theme_is_custom is False


def test_builtin_themes_use_exact_four_color_tokens() -> None:
    assert [theme.name for theme in BUILTIN_THEMES] == ["dark", "light", "cold", "warm"]
    for named_theme in BUILTIN_THEMES:
        assert set(named_theme.theme.as_dict()) == THEME_KEYS


def test_custom_theme_cycle_starts_with_custom_then_builtins() -> None:
    custom = Theme(
        background="#010101",
        panel_background="#020202",
        text="#fefefe",
        secondary_text="#777777",
    )

    cycle = theme_cycle(custom, custom_theme=True)

    assert [theme.name for theme in cycle] == ["custom", "dark", "light", "cold", "warm"]
    assert cycle[0].theme == custom


def test_missing_saved_theme_name_returns_none(tmp_path) -> None:
    assert load_saved_theme_name(tmp_path) is None


def test_saved_theme_name_round_trips(tmp_path) -> None:
    state_dir = tmp_path / "state" / "notui"

    save_theme_name(state_dir, "light")

    assert theme_state_path(state_dir).exists()
    assert load_saved_theme_name(state_dir) == "light"


def test_invalid_theme_state_returns_none(tmp_path) -> None:
    theme_state_path(tmp_path).write_text("active_theme = 42\n", encoding="utf-8")

    assert load_saved_theme_name(tmp_path) is None
