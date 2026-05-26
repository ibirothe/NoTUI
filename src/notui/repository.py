from __future__ import annotations

import sqlite3
from pathlib import Path

from notui.db import transaction
from notui.exceptions import NoTUIError, TodoNotFoundError
from notui.models import Todo


class RepositoryError(NoTUIError):
    """Persistence operation failed."""


def _row_to_todo(row: sqlite3.Row) -> Todo:
    return Todo(
        uuid=str(row["uuid"]),
        title=str(row["title"]),
        content=str(row["content"]),
        created_at=str(row["created_at"]),
        last_change=str(row["last_change"]),
        category=row["category"],
        is_deleted=bool(row["is_deleted"]),
        deleted_at=row["deleted_at"],
    )


class TodoRepository:
    def __init__(self, connection: sqlite3.Connection, db_path: Path | None = None) -> None:
        self.connection = connection
        self.db_path = db_path

    def insert(self, todo: Todo) -> Todo:
        try:
            with transaction(self.connection):
                self.connection.execute(
                    """
                    INSERT INTO todos
                    (
                        uuid, title, content, created_at, last_change,
                        category, is_deleted, deleted_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        todo.uuid,
                        todo.title,
                        todo.content,
                        todo.created_at,
                        todo.last_change,
                        todo.category,
                        int(todo.is_deleted),
                        todo.deleted_at,
                    ),
                )
            return todo
        except sqlite3.Error as exc:
            raise RepositoryError("Could not create note") from exc

    def get(self, uuid: str) -> Todo | None:
        row = self.connection.execute(
            """
            SELECT uuid, title, content, created_at, last_change, category, is_deleted, deleted_at
            FROM todos
            WHERE uuid = ?
            """,
            (uuid,),
        ).fetchone()
        return _row_to_todo(row) if row else None

    def list_active(self, limit: int = 500, offset: int = 0) -> list[Todo]:
        rows = self.connection.execute(
            """
            SELECT uuid, title, content, created_at, last_change, category, is_deleted, deleted_at
            FROM todos
            WHERE is_deleted = 0
            ORDER BY last_change DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ).fetchall()
        return [_row_to_todo(row) for row in rows]

    def search(self, query: str, limit: int = 500) -> list[Todo]:
        if not query.strip():
            return self.list_active(limit=limit)
        pattern = f"%{query.strip()}%"
        rows = self.connection.execute(
            """
            SELECT uuid, title, content, created_at, last_change, category, is_deleted, deleted_at
            FROM todos
            WHERE is_deleted = 0
              AND (
                lower(title) LIKE lower(?)
                OR lower(content) LIKE lower(?)
                OR lower(category) LIKE lower(?)
              )
            ORDER BY last_change DESC
            LIMIT ?
            """,
            (pattern, pattern, pattern, limit),
        ).fetchall()
        return [_row_to_todo(row) for row in rows]

    def update(self, todo: Todo) -> Todo:
        try:
            with transaction(self.connection):
                cursor = self.connection.execute(
                    """
                    UPDATE todos
                    SET title = ?, content = ?, category = ?, last_change = ?
                    WHERE uuid = ? AND is_deleted = 0
                    """,
                    (todo.title, todo.content, todo.category, todo.last_change, todo.uuid),
                )
                if cursor.rowcount != 1:
                    raise TodoNotFoundError(todo.uuid)
            return todo
        except sqlite3.Error as exc:
            raise RepositoryError("Could not update note") from exc

    def soft_delete(self, uuid: str, deleted_at: str, last_change: str) -> None:
        try:
            with transaction(self.connection):
                cursor = self.connection.execute(
                    """
                    UPDATE todos
                    SET is_deleted = 1, deleted_at = ?, last_change = ?
                    WHERE uuid = ? AND is_deleted = 0
                    """,
                    (deleted_at, last_change, uuid),
                )
                if cursor.rowcount != 1:
                    raise TodoNotFoundError(uuid)
        except sqlite3.Error as exc:
            raise RepositoryError("Could not delete note") from exc

    def count_active(self) -> int:
        row = self.connection.execute(
            "SELECT COUNT(*) AS count FROM todos WHERE is_deleted = 0"
        ).fetchone()
        return int(row["count"])
