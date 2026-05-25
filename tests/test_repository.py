from __future__ import annotations

import sqlite3

from notui.migrations import migrate
from notui.repository import TodoRepository
from notui.services import TodoService


def make_service() -> TodoService:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    migrate(connection)
    return TodoService(TodoRepository(connection))


def test_create_get_update_delete_todo() -> None:
    service = make_service()
    todo = service.create("First", "Body")
    fetched = service.get(todo.uuid)
    assert fetched.title == "First"
    assert fetched.created_at.endswith("Z")
    assert fetched.last_change.endswith("Z")

    updated = service.update(todo.uuid, "Changed", "New body")
    assert updated.uuid == todo.uuid
    assert updated.created_at == todo.created_at
    assert updated.last_change >= todo.last_change

    service.soft_delete(todo.uuid)
    assert service.list_active() == []


def test_search_matches_title_and_content() -> None:
    service = make_service()
    service.create("Alpha", "nothing")
    service.create("Beta", "needle")

    assert [todo.title for todo in service.search("alpha")] == ["Alpha"]
    assert [todo.title for todo in service.search("needle")] == ["Beta"]
