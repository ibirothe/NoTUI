from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Todo:
    uuid: str
    title: str
    content: str
    created_at: str
    last_change: str
    category: str | None = None
    is_deleted: bool = False
    deleted_at: str | None = None
