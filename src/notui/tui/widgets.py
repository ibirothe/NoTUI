from __future__ import annotations

from textual.widgets import Label, ListItem, Static

from notui.models import Todo


class TodoListItem(ListItem):
    def __init__(self, todo: Todo) -> None:
        super().__init__(Label(todo.title))
        self.todo_uuid = todo.uuid


class DetailPanel(Static):
    def show_empty(self, search_active: bool = False) -> None:
        if search_active:
            self.update("No matching todos.\nEscape clears search.")
        else:
            self.update("No todos yet.\nPress n to create one.")

    def show_todo(self, todo: Todo) -> None:
        content = todo.content or ""
        self.update(
            f"{todo.title}\n\n"
            f"Created: {todo.created_at}\n"
            f"Changed: {todo.last_change}\n\n"
            f"Content\n{content}"
        )
