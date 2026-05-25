from __future__ import annotations

import uuid
from dataclasses import replace

from notui.exceptions import TodoNotFoundError, ValidationError
from notui.models import Todo
from notui.repository import TodoRepository
from notui.time import utc_now

MAX_TITLE_LENGTH = 200
MAX_CONTENT_LENGTH = 100_000


def validate_title(title: str) -> str:
    normalized = title.strip()
    if not normalized:
        raise ValidationError("Title is required")
    if "\n" in normalized or "\r" in normalized:
        raise ValidationError("Title must be a single line")
    if len(normalized) > MAX_TITLE_LENGTH:
        raise ValidationError(f"Title must be {MAX_TITLE_LENGTH} characters or fewer")
    return normalized


def validate_content(content: str) -> str:
    if len(content) > MAX_CONTENT_LENGTH:
        raise ValidationError(f"Content must be {MAX_CONTENT_LENGTH} characters or fewer")
    return content


class TodoService:
    def __init__(self, repository: TodoRepository) -> None:
        self.repository = repository

    def create(self, title: str, content: str = "") -> Todo:
        now = utc_now()
        todo = Todo(
            uuid=str(uuid.uuid4()),
            title=validate_title(title),
            content=validate_content(content),
            created_at=now,
            last_change=now,
        )
        return self.repository.insert(todo)

    def get(self, todo_uuid: str) -> Todo:
        todo = self.repository.get(todo_uuid)
        if todo is None or todo.is_deleted:
            raise TodoNotFoundError(todo_uuid)
        return todo

    def list_active(self, limit: int = 500, offset: int = 0) -> list[Todo]:
        return self.repository.list_active(limit=limit, offset=offset)

    def search(self, query: str, limit: int = 500) -> list[Todo]:
        return self.repository.search(query=query, limit=limit)

    def update(self, todo_uuid: str, title: str, content: str) -> Todo:
        existing = self.get(todo_uuid)
        updated = replace(
            existing,
            title=validate_title(title),
            content=validate_content(content),
            last_change=utc_now(),
        )
        return self.repository.update(updated)

    def soft_delete(self, todo_uuid: str) -> None:
        now = utc_now()
        self.repository.soft_delete(todo_uuid, deleted_at=now, last_change=now)

    def count_active(self) -> int:
        return self.repository.count_active()
