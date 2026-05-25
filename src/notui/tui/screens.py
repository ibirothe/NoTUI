from __future__ import annotations

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.events import Resize
from textual.screen import ModalScreen, Screen
from textual.timer import Timer
from textual.widgets import Input, ListView, Static, TextArea

from notui.exceptions import NoTUIError, ValidationError
from notui.models import Todo
from notui.services import TodoService
from notui.tui.widgets import DetailPanel, TodoListItem


class HelpModal(ModalScreen[None]):
    BINDINGS = [("escape", "dismiss", "Close"), ("q", "quit", "Quit"), ("Q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        with Container(classes="modal"):
            yield Static(
                "Keyboard help\n\n"
                "q quit    ? help    n new    enter open\n"
                "e edit    d delete  / search r refresh\n"
                "j/down move down    k/up move up\n"
                "g first   G last    escape cancel or clear\n"
                "ctrl+s save in editor    ctrl+t cycle theme",
            )

    def action_dismiss(self) -> None:
        self.dismiss(None)

    def action_quit(self) -> None:
        self.app.exit()


class ConfirmDeleteModal(ModalScreen[bool]):
    BINDINGS = [
        ("y", "confirm", "Yes"),
        ("n", "cancel", "No"),
        ("escape", "cancel", "Cancel"),
        ("q", "quit", "Quit"),
        ("Q", "quit", "Quit"),
    ]

    def __init__(self, title: str) -> None:
        super().__init__()
        self.title = title

    def compose(self) -> ComposeResult:
        with Container(classes="modal"):
            yield Static(
                f"Delete note?\n\n{self.title}\n\nPress y to delete, n or escape to cancel."
            )

    def action_confirm(self) -> None:
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)

    def action_quit(self) -> None:
        self.dismiss(False)
        self.app.exit()


class DiscardChangesModal(ModalScreen[bool]):
    BINDINGS = [
        ("y", "discard", "Discard"),
        ("n", "cancel", "Cancel"),
        ("escape", "cancel", "Cancel"),
        ("q", "quit", "Quit"),
        ("Q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        with Container(classes="modal"):
            yield Static(
                "Discard unsaved changes?\n\nPress y to discard, n or escape to keep editing."
            )

    def action_discard(self) -> None:
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)

    def action_quit(self) -> None:
        self.dismiss(False)
        self.app.exit()


class EditorScreen(Screen[bool]):
    BINDINGS = [
        ("ctrl+s", "save", "Save"),
        ("escape", "cancel", "Cancel"),
        ("q", "quit", "Quit"),
        ("Q", "quit", "Quit"),
    ]

    def __init__(self, service: TodoService, todo: Todo | None = None) -> None:
        super().__init__()
        self.service = service
        self.todo = todo
        self.initial_title = todo.title if todo else ""
        self.initial_content = todo.content if todo else ""
        self.dirty = False

    def compose(self) -> ComposeResult:
        with Vertical(classes="panel"):
            yield Static("Editor", classes="panel-title")
            yield Input(value=self.initial_title, placeholder="Title", id="editor-title")
            yield TextArea(self.initial_content, id="editor-content")
            yield Static("edit  ctrl+s save  escape cancel", id="editor-status", classes="status")

    def on_mount(self) -> None:
        self.query_one("#editor-title", Input).focus()

    @on(Input.Changed)
    @on(TextArea.Changed)
    def mark_dirty(self) -> None:
        self.dirty = True
        self.query_one("#editor-status", Static).update("edit  unsaved  ctrl+s save  escape cancel")

    def _values(self) -> tuple[str, str]:
        title = self.query_one("#editor-title", Input).value
        content = self.query_one("#editor-content", TextArea).text
        return title, content

    def action_save(self) -> None:
        title, content = self._values()
        try:
            if self.todo is None:
                self.service.create(title, content)
            else:
                self.service.update(self.todo.uuid, title, content)
        except ValidationError as exc:
            self.query_one("#editor-status", Static).update(f"edit  {exc}")
            return
        self.dirty = False
        self.query_one("#editor-status", Static).update("edit  Saved")
        self.dismiss(True)

    def action_cancel(self) -> None:
        if not self.dirty:
            self.dismiss(False)
            return

        def on_answer(discard: bool | None) -> None:
            if discard:
                self.dismiss(False)

        self.app.push_screen(DiscardChangesModal(), on_answer)

    def action_quit(self) -> None:
        self.app.exit()


class ErrorScreen(Screen[None]):
    BINDINGS = [("q", "quit", "Quit"), ("Q", "quit", "Quit")]

    def __init__(self, message: str) -> None:
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        with Container(classes="modal"):
            yield Static(self.message)

    def action_quit(self) -> None:
        self.app.exit()


class MainScreen(Screen[None]):
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("Q", "quit", "Quit"),
        ("?", "help", "Help"),
        ("n", "new_todo", "New"),
        ("enter", "open_selected", "Open"),
        ("e", "edit_selected", "Edit"),
        ("d", "delete_selected", "Delete"),
        ("/", "search", "Search"),
        ("escape", "escape", "Escape"),
        ("j", "cursor_down", "Down"),
        ("down", "cursor_down", "Down"),
        ("k", "cursor_up", "Up"),
        ("up", "cursor_up", "Up"),
        ("g", "first", "First"),
        ("G", "last", "Last"),
        ("r", "refresh", "Refresh"),
        ("ctrl+t", "cycle_theme", "Theme"),
    ]

    def __init__(self, service: TodoService) -> None:
        super().__init__()
        self.service = service
        self.todos: list[Todo] = []
        self.selected_uuid: str | None = None
        self.search_query = ""
        self.search_timer: Timer | None = None
        self.search_active = False

    def compose(self) -> ComposeResult:
        with Horizontal(id="topbar"):
            yield Static("NoTUI", id="brand")
            yield Static("n new  ctrl+t theme  ? help", id="top-hints")
        with Horizontal(id="searchbar"):
            yield Static("FILTER", id="search-label")
            yield Input(placeholder="Press / to search title and content", id="search")
        with Horizontal(id="main"):
            with Vertical(id="list-panel", classes="panel"):
                yield Static("Note list", classes="panel-title")
                yield ListView(id="todo-list")
            with Vertical(id="detail-panel", classes="panel"):
                yield Static("Detail / editor", classes="panel-title")
                yield DetailPanel(id="detail")
        yield Static(
            "list  up/down move  enter open  e edit  ctrl+t theme  / search  q quit",
            id="status",
            classes="status",
        )

    def on_mount(self) -> None:
        self.query_one("#searchbar", Horizontal).display = False
        self.query_one("#search", Input).disabled = True
        self._apply_responsive_layout()
        self.refresh_todos()

    def on_resize(self, event: Resize) -> None:
        self._apply_responsive_layout()

    def _apply_responsive_layout(self) -> None:
        width = self.size.width
        stacked = width < 100
        main = self.query_one("#main", Horizontal)
        list_panel = self.query_one("#list-panel", Vertical)
        detail_panel = self.query_one("#detail-panel", Vertical)
        main.set_class(stacked, "stacked")
        list_panel.set_class(stacked, "stacked-panel")
        detail_panel.set_class(stacked, "stacked-panel")
        detail_panel.display = width >= 70

    def refresh_todos(self) -> None:
        try:
            self.todos = self.service.search(self.search_query)
        except NoTUIError as exc:
            self.query_one("#status", Static).update(f"list  {exc}")
            return

        list_view = self.query_one("#todo-list", ListView)
        list_view.clear()
        for todo in self.todos:
            list_view.append(TodoListItem(todo))

        visible_uuids = {todo.uuid for todo in self.todos}
        if self.selected_uuid is not None and self.selected_uuid in visible_uuids:
            list_view.index = next(
                index for index, todo in enumerate(self.todos) if todo.uuid == self.selected_uuid
            )
            self._show_selected_detail()
        else:
            self.selected_uuid = None
            list_view.index = None
            self.query_one("#detail", DetailPanel).show_empty(search_active=bool(self.search_query))

        total = self.service.count_active()
        suffix = "  showing latest 500" if total > 500 and not self.search_query else ""
        mode = "search" if self.search_query else "list"
        self.query_one("#status", Static).update(
            f"{mode}  {len(self.todos)} visible  {total} active{suffix}"
        )
        self._update_search_label()

    def _update_search_label(self) -> None:
        label = "SEARCH" if self.search_active else "FILTER"
        self.query_one("#search-label", Static).update(label)

    def selected_todo(self) -> Todo | None:
        if self.selected_uuid is None:
            return None
        return next((todo for todo in self.todos if todo.uuid == self.selected_uuid), None)

    def _show_selected_detail(self) -> None:
        todo = self.selected_todo()
        if todo is None:
            self.query_one("#detail", DetailPanel).show_empty(search_active=bool(self.search_query))
        else:
            self.query_one("#detail", DetailPanel).show_todo(todo)

    @on(ListView.Highlighted)
    def on_list_highlighted(self, event: ListView.Highlighted) -> None:
        item = event.item
        if item is not None and hasattr(item, "todo_uuid"):
            self.selected_uuid = item.todo_uuid
            self._show_selected_detail()

    @on(Input.Changed, "#search")
    def on_search_changed(self, event: Input.Changed) -> None:
        self.search_query = event.value
        if self.search_timer is not None:
            self.search_timer.stop()
        self.search_timer = self.set_timer(0.15, self.refresh_todos)

    def _after_editor(self, saved: bool | None) -> None:
        if saved:
            self.refresh_todos()
            self.query_one("#status", Static).update("list  Saved")

    def action_help(self) -> None:
        self.app.push_screen(HelpModal())

    def action_quit(self) -> None:
        self.app.exit()

    def action_new_todo(self) -> None:
        self.app.push_screen(EditorScreen(self.service), self._after_editor)

    def action_open_selected(self) -> None:
        self.action_edit_selected()

    def action_edit_selected(self) -> None:
        todo = self.selected_todo()
        if todo is not None:
            self.app.push_screen(EditorScreen(self.service, todo), self._after_editor)

    def action_delete_selected(self) -> None:
        todo = self.selected_todo()
        if todo is None:
            return

        def on_confirm(confirmed: bool | None) -> None:
            if confirmed:
                self.service.soft_delete(todo.uuid)
                self.refresh_todos()
                self.query_one("#status", Static).update("list  Deleted")

        self.app.push_screen(ConfirmDeleteModal(todo.title), on_confirm)

    def action_search(self) -> None:
        search = self.query_one("#search", Input)
        self.search_active = True
        self.query_one("#searchbar", Horizontal).display = True
        search.disabled = False
        search.focus()
        self._update_search_label()
        self.query_one("#status", Static).update("search  typing filters  escape clears")

    def action_escape(self) -> None:
        search = self.query_one("#search", Input)
        if self.search_active or self.search_query:
            search.value = ""
            search.disabled = True
            self.search_active = False
            self.search_query = ""
            self.query_one("#searchbar", Horizontal).display = False
            self.refresh_todos()
            self._update_search_label()
            self.query_one("#todo-list", ListView).focus()

    def action_cursor_down(self) -> None:
        self.query_one("#todo-list", ListView).action_cursor_down()

    def action_cursor_up(self) -> None:
        self.query_one("#todo-list", ListView).action_cursor_up()

    def action_first(self) -> None:
        if self.todos:
            self.query_one("#todo-list", ListView).index = 0

    def action_last(self) -> None:
        if self.todos:
            self.query_one("#todo-list", ListView).index = len(self.todos) - 1

    def action_refresh(self) -> None:
        self.refresh_todos()

    def action_cycle_theme(self) -> None:
        cycle_theme = getattr(self.app, "cycle_theme", None)
        if cycle_theme is None:
            return
        theme_name = cycle_theme()
        self.query_one("#status", Static).update(f"list  Theme: {theme_name}")
