from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Label, ListItem, Static

from notui.models import Todo

NOTUI_LOGO = """███▄▄▄▄    ▄██████▄      ███     ███    █▄   ▄█
███▀▀▀██▄ ███    ███ ▀█████████▄ ███    ███ ███
███   ███ ███    ███    ▀███▀▀██ ███    ███ ███▌
███   ███ ███    ███     ███   ▀ ███    ███ ███▌
███   ███ ███    ███     ███     ███    ███ ███▌
███   ███ ███    ███     ███     ███    ███ ███
███   ███ ███    ███     ███     ███    ███ ███
 ▀█   █▀   ▀██████▀     ▄████▀   ████████▀  █▀"""


class TodoListItem(ListItem):
    def __init__(self, todo: Todo) -> None:
        super().__init__(Label(todo.title))
        self.todo_uuid = todo.uuid


class DetailPanel(Vertical):
    def compose(self) -> ComposeResult:
        yield Static(NOTUI_LOGO, id="detail-logo")
        yield Static("", id="detail-title")
        yield Static("", id="detail-created", classes="muted")
        yield Static("", id="detail-changed", classes="muted")
        yield Static("", id="detail-content")

    def on_mount(self) -> None:
        self.show_empty()

    def show_empty(self, search_active: bool = False) -> None:
        self.query_one("#detail-title", Static).display = False
        self.query_one("#detail-created", Static).display = False
        self.query_one("#detail-changed", Static).display = False
        self.query_one("#detail-content", Static).display = False
        logo = self.query_one("#detail-logo", Static)
        logo.display = True
        if search_active:
            logo.update("No matching notes.\nEscape clears search.")
        else:
            logo.update(NOTUI_LOGO)

    def show_todo(self, todo: Todo) -> None:
        content = todo.content or ""
        self.query_one("#detail-logo", Static).display = False
        title = self.query_one("#detail-title", Static)
        created = self.query_one("#detail-created", Static)
        changed = self.query_one("#detail-changed", Static)
        detail_content = self.query_one("#detail-content", Static)
        title.display = True
        created.display = True
        changed.display = True
        detail_content.display = True
        title.update(todo.title)
        created.update(f"Created: {todo.created_at}")
        changed.update(f"Changed: {todo.last_change}")
        detail_content.update(f"\nContent\n{content}")
