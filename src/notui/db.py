from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from notui.exceptions import DatabaseOpenError


def open_connection(path: Path) -> sqlite3.Connection:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA synchronous = NORMAL")
        connection.execute("PRAGMA busy_timeout = 3000")
        return connection
    except sqlite3.Error as exc:
        raise DatabaseOpenError(f"Could not open local note database at {path}") from exc
    except OSError as exc:
        raise DatabaseOpenError(f"Could not create database directory for {path}") from exc


@contextmanager
def transaction(connection: sqlite3.Connection) -> Iterator[None]:
    try:
        connection.execute("BEGIN")
        yield
    except Exception:
        connection.rollback()
        raise
    else:
        connection.commit()
