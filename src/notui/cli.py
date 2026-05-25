from __future__ import annotations

import argparse
import logging
import os
import sys
from importlib import metadata
from pathlib import Path

from notui import __version__
from notui.app import NoTUIApp
from notui.config import AppConfig, default_log_path, load_config, resolve_db_path
from notui.db import open_connection
from notui.exceptions import ConfigError, DatabaseOpenError, MigrationError
from notui.migrations import migrate
from notui.repository import TodoRepository
from notui.services import TodoService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="notui")
    parser.add_argument("--db", type=Path, help="Override SQLite database path")
    parser.add_argument("--config", type=Path, help="Override config file path")
    parser.add_argument("--version", action="version", version=f"NoTUI {__version__}")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("doctor", help="Print diagnostics")
    return parser


def setup_logging() -> Path:
    log_path = default_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    return log_path


def _textual_version() -> str:
    try:
        return metadata.version("textual")
    except metadata.PackageNotFoundError:
        return "not installed"


def _is_writable(path: Path) -> bool:
    target = path if path.exists() else path.parent
    return os.access(target, os.W_OK)


def doctor(config: AppConfig, db_path: Path) -> int:
    print(f"NoTUI version: {__version__}")
    print(f"Python version: {sys.version.split()[0]}")
    print(f"Textual version: {_textual_version()}")
    print(f"Database path: {db_path}")
    print(f"Database exists: {'yes' if db_path.exists() else 'no'}")
    print(f"Database writable: {'yes' if _is_writable(db_path) else 'no'}")
    print(f"Config path: {config.config_path}")
    print("Resolved theme colors:")
    for key, value in config.theme.as_dict().items():
        print(f"  {key}: {value}")
    return 0


def _startup_error(message: str, db_path: Path | None = None, log_path: Path | None = None) -> str:
    parts = [message]
    if db_path is not None:
        parts.append(f"Path: {db_path}")
    if log_path is not None:
        parts.append(f"Log: {log_path}")
    parts.append("Press q to quit.")
    return "\n".join(parts)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    log_path = setup_logging()

    try:
        config = load_config(args.config)
        db_path = resolve_db_path(config, args.db)
    except ConfigError as exc:
        logging.exception("Configuration failed")
        print(f"Config error: {exc}", file=sys.stderr)
        return 2

    if args.command == "doctor":
        return doctor(config, db_path)

    try:
        connection = open_connection(db_path)
        migrate(connection)
    except (DatabaseOpenError, MigrationError):
        logging.exception("Startup failed")
        NoTUIApp(
            theme=config.theme,
            custom_theme=config.theme_is_custom,
            state_dir=config.state_dir,
            startup_error=_startup_error(
                "Could not open local note database.",
                db_path=db_path,
                log_path=log_path,
            ),
        ).run()
        return 1

    try:
        repository = TodoRepository(connection, db_path=db_path)
        service = TodoService(repository)
        NoTUIApp(
            service=service,
            theme=config.theme,
            custom_theme=config.theme_is_custom,
            state_dir=config.state_dir,
        ).run()
        return 0
    finally:
        connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
