from __future__ import annotations

from notui.db import open_connection
from notui.migrations import migrate


def test_fresh_database_startup_creates_schema(tmp_path) -> None:
    db_path = tmp_path / "todos.sqlite"
    connection = open_connection(db_path)
    migrate(connection)
    migrate(connection)
    rows = connection.execute("SELECT version FROM schema_version").fetchall()
    assert [row["version"] for row in rows] == [1]
    assert db_path.exists()
