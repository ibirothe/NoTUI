from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Label, ListItem, ListView, Static

from notui.models import Todo
from notui.time import format_display_time

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


class CategoryHeaderItem(ListItem):
    def __init__(self, category: str) -> None:
        super().__init__(Label(f"{category}:"), classes="category-header", disabled=True)


class TodoListView(ListView):
    def action_cursor_down(self) -> None:
        if self.index is None:
            self._select_first()
            return
        super().action_cursor_down()

    def action_cursor_up(self) -> None:
        if self.index is None:
            self._select_last()
            return
        super().action_cursor_up()

    def _select_first(self) -> None:
        for index, item in enumerate(self.children):
            if not getattr(item, "disabled", False):
                self.index = index
                return

    def _select_last(self) -> None:
        for index, item in reversed(list(enumerate(self.children))):
            if not getattr(item, "disabled", False):
                self.index = index
                return


class DetailPanel(Vertical):
    def compose(self) -> ComposeResult:
        yield Static(NOTUI_LOGO, id="detail-logo")
        yield Static("", id="detail-title")
        yield Static("", id="detail-category", classes="muted")
        yield Static("", id="detail-created", classes="muted")
        yield Static("", id="detail-changed", classes="muted")
        yield Static("", id="detail-content")

    def on_mount(self) -> None:
        self.show_empty()

    def show_empty(self, search_active: bool = False) -> None:
        self.query_one("#detail-title", Static).display = False
        self.query_one("#detail-category", Static).display = False
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
        category = self.query_one("#detail-category", Static)
        created = self.query_one("#detail-created", Static)
        changed = self.query_one("#detail-changed", Static)
        detail_content = self.query_one("#detail-content", Static)
        title.display = True
        category.display = todo.category is not None
        created.display = True
        changed.display = True
        detail_content.display = True
        title.update(todo.title)
        category.update(f"Category: {todo.category or ''}")
        created.update(f"Created: {format_display_time(todo.created_at)}")
        changed.update(f"Changed: {format_display_time(todo.last_change)}")
        detail_content.update(f"\n{content}")
