from __future__ import annotations

import sqlite3

from notui.db import open_connection
from notui.migrations import MIGRATION_1, migrate


def test_fresh_database_startup_creates_schema(tmp_path) -> None:
    db_path = tmp_path / "todos.sqlite"
    connection = open_connection(db_path)
    migrate(connection)
    migrate(connection)
    rows = connection.execute("SELECT version FROM schema_version").fetchall()
    assert [row["version"] for row in rows] == [1, 2]
    assert db_path.exists()


def test_existing_v1_database_migrates_to_category_schema() -> None:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute(
        """
        CREATE TABLE schema_version (
            version INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL
        )
        """
    )
    for statement in MIGRATION_1:
        connection.execute(statement)
    connection.execute(
        "INSERT INTO schema_version (version, applied_at) VALUES (?, ?)",
        (1, "2026-05-25T00:00:00Z"),
    )
    connection.commit()

    migrate(connection)

    columns = {
        row["name"]: row
        for row in connection.execute("PRAGMA table_info(todos)").fetchall()
    }
    rows = connection.execute("SELECT version FROM schema_version").fetchall()
    assert "category" in columns
    assert [row["version"] for row in rows] == [1, 2]
