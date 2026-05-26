from __future__ import annotations

import sqlite3

from notui.db import transaction
from notui.exceptions import MigrationError
from notui.time import utc_now

MIGRATION_1 = (
    """
    CREATE TABLE IF NOT EXISTS todos (
        uuid TEXT PRIMARY KEY NOT NULL,
        title TEXT NOT NULL CHECK (length(trim(title)) > 0),
        content TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL,
        last_change TEXT NOT NULL,
        is_deleted INTEGER NOT NULL DEFAULT 0 CHECK (is_deleted IN (0, 1)),
        deleted_at TEXT
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_todos_last_change
    ON todos (last_change DESC)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_todos_not_deleted_last_change
    ON todos (is_deleted, last_change DESC)
    """,
)

MIGRATION_2 = (
    """
    ALTER TABLE todos
    ADD COLUMN category TEXT
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_todos_not_deleted_category_last_change
    ON todos (is_deleted, category, last_change DESC)
    """,
)


def migrate(connection: sqlite3.Connection) -> None:
    try:
        with transaction(connection):
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT NOT NULL
                )
                """
            )
            current = connection.execute(
                "SELECT COALESCE(MAX(version), 0) AS version FROM schema_version"
            ).fetchone()["version"]
            if current < 1:
                for statement in MIGRATION_1:
                    connection.execute(statement)
                connection.execute(
                    "INSERT INTO schema_version (version, applied_at) VALUES (?, ?)",
                    (1, utc_now()),
                )
            if current < 2:
                for statement in MIGRATION_2:
                    connection.execute(statement)
                connection.execute(
                    "INSERT INTO schema_version (version, applied_at) VALUES (?, ?)",
                    (2, utc_now()),
                )
    except sqlite3.Error as exc:
        raise MigrationError("Could not migrate local note database") from exc
