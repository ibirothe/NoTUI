from __future__ import annotations

import os
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from platformdirs import user_config_dir, user_data_dir, user_state_dir

from notui.exceptions import ConfigError

APP_NAME = "notui"
DEFAULT_DB_NAME = "notui.sqlite"
THEME_STATE_NAME = "theme.toml"

THEME_KEYS = frozenset({"background", "panel_background", "text", "secondary_text"})
HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
THEME_NAME_RE = re.compile(r"^[A-Za-z0-9_-]+$")


@dataclass(frozen=True, slots=True)
class Theme:
    background: str = "#0b0b0b"
    panel_background: str = "#151515"
    text: str = "#e8e8e8"
    secondary_text: str = "#8a8a8a"

    @classmethod
    def from_mapping(cls, values: dict[str, Any]) -> Theme:
        extra = set(values) - THEME_KEYS
        missing = THEME_KEYS - set(values)
        if extra:
            raise ConfigError(f"Unknown theme color keys: {', '.join(sorted(extra))}")
        if missing:
            raise ConfigError(f"Missing theme color keys: {', '.join(sorted(missing))}")
        for key, value in values.items():
            if not isinstance(value, str) or not HEX_COLOR_RE.match(value):
                raise ConfigError(f"Theme color {key!r} must be a #RRGGBB hex color")
        return cls(**{key: str(values[key]).lower() for key in THEME_KEYS})

    def as_dict(self) -> dict[str, str]:
        return {
            "background": self.background,
            "panel_background": self.panel_background,
            "text": self.text,
            "secondary_text": self.secondary_text,
        }


@dataclass(frozen=True, slots=True)
class UIConfig:
    confirm_delete: bool = True
    autosave_on_blur: bool = False


@dataclass(frozen=True, slots=True)
class AppConfig:
    database_path: Path | None
    theme: Theme
    theme_is_custom: bool
    ui: UIConfig
    config_path: Path
    state_dir: Path


def default_config_path() -> Path:
    return Path(user_config_dir(APP_NAME, ensure_exists=True)) / "config.toml"


def default_data_dir() -> Path:
    return Path(user_data_dir(APP_NAME, ensure_exists=True))


def default_state_dir() -> Path:
    return Path(user_state_dir(APP_NAME, ensure_exists=True))


def default_db_path() -> Path:
    return default_data_dir() / DEFAULT_DB_NAME


def default_log_path() -> Path:
    return default_state_dir() / "notui.log"


def theme_state_path(state_dir: Path) -> Path:
    return state_dir / THEME_STATE_NAME


def load_saved_theme_name(state_dir: Path) -> str | None:
    path = theme_state_path(state_dir)
    if not path.exists():
        return None
    try:
        with path.open("rb") as handle:
            data = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError):
        return None
    theme_name = data.get("active_theme")
    return theme_name if isinstance(theme_name, str) else None


def save_theme_name(state_dir: Path, theme_name: str) -> None:
    if not THEME_NAME_RE.match(theme_name):
        return
    try:
        state_dir.mkdir(parents=True, exist_ok=True)
        theme_state_path(state_dir).write_text(f'active_theme = "{theme_name}"\n', encoding="utf-8")
    except OSError:
        return


def _read_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with path.open("rb") as handle:
            data = tomllib.load(handle)
    except OSError as exc:
        raise ConfigError(f"Could not read config file: {path}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"Invalid TOML config file: {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError("Config root must be a table")
    return data


def load_config(config_path: Path | None = None) -> AppConfig:
    path = (config_path or default_config_path()).expanduser()
    data = _read_config(path)

    allowed_sections = {"database", "theme", "ui"}
    extra_sections = set(data) - allowed_sections
    if extra_sections:
        raise ConfigError(f"Unknown config sections: {', '.join(sorted(extra_sections))}")

    theme = Theme()
    theme_is_custom = False
    if "theme" in data:
        if not isinstance(data["theme"], dict):
            raise ConfigError("[theme] must be a table")
        theme = Theme.from_mapping(data["theme"])
        theme_is_custom = True

    ui = UIConfig()
    if "ui" in data:
        raw_ui = data["ui"]
        if not isinstance(raw_ui, dict):
            raise ConfigError("[ui] must be a table")
        allowed_ui = {"confirm_delete", "autosave_on_blur"}
        extra_ui = set(raw_ui) - allowed_ui
        if extra_ui:
            raise ConfigError(f"Unknown ui keys: {', '.join(sorted(extra_ui))}")
        ui = UIConfig(
            confirm_delete=bool(raw_ui.get("confirm_delete", True)),
            autosave_on_blur=bool(raw_ui.get("autosave_on_blur", False)),
        )

    database_path: Path | None = None
    if "database" in data:
        raw_database = data["database"]
        if not isinstance(raw_database, dict):
            raise ConfigError("[database] must be a table")
        extra_database = set(raw_database) - {"path"}
        if extra_database:
            raise ConfigError(f"Unknown database keys: {', '.join(sorted(extra_database))}")
        raw_path = raw_database.get("path", "")
        if raw_path:
            if not isinstance(raw_path, str):
                raise ConfigError("database.path must be a string")
            database_path = Path(os.path.expandvars(raw_path)).expanduser()

    return AppConfig(
        database_path=database_path,
        theme=theme,
        theme_is_custom=theme_is_custom,
        ui=ui,
        config_path=path,
        state_dir=default_state_dir(),
    )


def resolve_db_path(config: AppConfig, cli_db_path: Path | None = None) -> Path:
    if cli_db_path is not None:
        return cli_db_path.expanduser()
    if config.database_path is not None:
        return config.database_path
    return default_db_path()
