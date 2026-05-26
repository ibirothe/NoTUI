from __future__ import annotations

import asyncio
from contextlib import suppress

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.events import Resize
from textual.screen import ModalScreen, Screen
from textual.timer import Timer
from textual.widgets import Input, ListView, Static, TextArea

from notui.clipboard import ClipboardError, copy_text, paste_text
from notui.exceptions import NoTUIError, ValidationError
from notui.models import Todo
from notui.script_runner import run_note_script
from notui.services import TodoService
from notui.tui.widgets import CategoryHeaderItem, DetailPanel, TodoListItem, TodoListView


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
                "ctrl+x run note content     ctrl+c copy note content\n"
                "ctrl+v paste as note\n"
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


class ConfirmExecuteModal(ModalScreen[bool]):
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
                "Execute note as shell script?\n\n"
                f"{self.title}\n\n"
                "Press y to execute, n or escape to cancel."
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

    def __init__(
        self,
        service: TodoService,
        todo: Todo | None = None,
        initial_content: str = "",
    ) -> None:
        super().__init__()
        self.service = service
        self.todo = todo
        self.initial_title = todo.title if todo else ""
        self.initial_category = todo.category if todo and todo.category else ""
        self.initial_content = todo.content if todo else initial_content
        self.dirty = todo is None and bool(initial_content)

    def compose(self) -> ComposeResult:
        with Vertical(classes="panel"):
            yield Static("Editor", classes="panel-title")
            yield Input(value=self.initial_title, placeholder="Title", id="editor-title")
            yield Input(value=self.initial_category, placeholder="Category", id="editor-category")
            yield TextArea(self.initial_content, id="editor-content")
            yield Static("edit  ctrl+s save  escape cancel", id="editor-status", classes="status")

    def on_mount(self) -> None:
        self.query_one("#editor-title", Input).focus()

    @on(Input.Changed)
    @on(TextArea.Changed)
    def mark_dirty(self) -> None:
        self.dirty = True
        self.query_one("#editor-status", Static).update("edit  unsaved  ctrl+s save  escape cancel")

    def _values(self) -> tuple[str, str, str]:
        title = self.query_one("#editor-title", Input).value
        category = self.query_one("#editor-category", Input).value
        content = self.query_one("#editor-content", TextArea).text
        return title, category, content

    def action_save(self) -> None:
        title, category, content = self._values()
        try:
            if self.todo is None:
                self.service.create(title, content, category=category)
            else:
                self.service.update(self.todo.uuid, title, content, category=category)
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
        ("ctrl+c", "copy_selected_content", "Copy"),
        ("ctrl+v", "paste_clipboard_note", "Paste"),
        ("ctrl+x", "execute_selected_content", "Execute"),
    ]

    def __init__(self, service: TodoService) -> None:
        super().__init__()
        self.service = service
        self.todos: list[Todo] = []
        self.todo_row_indices: dict[str, int] = {}
        self.selected_uuid: str | None = None
        self.search_query = ""
        self.search_timer: Timer | None = None
        self.search_active = False

    def compose(self) -> ComposeResult:
        with Horizontal(id="topbar"):
            yield Static("NoTUI", id="brand")
            yield Static("n new  ctrl+x run  ctrl+c copy  ctrl+v paste  ? help", id="top-hints")
        with Horizontal(id="searchbar"):
            yield Static("FILTER", id="search-label")
            yield Input(placeholder="Press / to search title and content", id="search")
        with Horizontal(id="main"):
            with Vertical(id="list-panel", classes="panel"):
                yield Static("Note list", classes="panel-title")
                yield TodoListView(id="todo-list")
            with Vertical(id="detail-panel", classes="panel"):
                yield DetailPanel(id="detail")
        yield Static(
            "list  up/down move  enter open  e edit  ctrl+x run  ctrl+c copy  q quit",
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
        self.todo_row_indices = {}
        row_index = 0
        for category, todos in self._group_todos_for_display():
            if category is not None:
                list_view.append(CategoryHeaderItem(category))
                row_index += 1
            for todo in todos:
                list_view.append(TodoListItem(todo))
                self.todo_row_indices[todo.uuid] = row_index
                row_index += 1

        visible_uuids = {todo.uuid for todo in self.todos}
        if self.selected_uuid is not None and self.selected_uuid in visible_uuids:
            list_view.index = self.todo_row_indices[self.selected_uuid]
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

    def _group_todos_for_display(self) -> list[tuple[str | None, list[Todo]]]:
        categorized: dict[str, list[Todo]] = {}
        uncategorized: list[Todo] = []
        for todo in self.todos:
            if todo.category is None:
                uncategorized.append(todo)
            else:
                categorized.setdefault(todo.category, []).append(todo)

        groups: list[tuple[str | None, list[Todo]]] = list(categorized.items())
        if uncategorized:
            groups.append((None, uncategorized))
        return groups

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
        elif item is not None:
            selectable_indices = self._selectable_list_indices()
            if selectable_indices:
                self.query_one("#todo-list", ListView).index = selectable_indices[0]

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
        self._move_cursor(1)

    def action_cursor_up(self) -> None:
        self._move_cursor(-1)

    def action_first(self) -> None:
        selectable_indices = self._selectable_list_indices()
        if selectable_indices:
            self.query_one("#todo-list", ListView).index = selectable_indices[0]

    def action_last(self) -> None:
        selectable_indices = self._selectable_list_indices()
        if selectable_indices:
            self.query_one("#todo-list", ListView).index = selectable_indices[-1]

    def _move_cursor(self, direction: int) -> None:
        list_view = self.query_one("#todo-list", ListView)
        selectable_indices = self._selectable_list_indices()
        if not selectable_indices:
            return
        if list_view.index is None:
            list_view.index = selectable_indices[0] if direction > 0 else selectable_indices[-1]
            return

        candidates = (
            (index for index in selectable_indices if index > list_view.index)
            if direction > 0
            else (index for index in reversed(selectable_indices) if index < list_view.index)
        )
        with suppress(StopIteration):
            list_view.index = next(candidates)

    def _selectable_list_indices(self) -> list[int]:
        list_view = self.query_one("#todo-list", ListView)
        return [
            index
            for index, item in enumerate(list_view.children)
            if not getattr(item, "disabled", False)
        ]

    def action_refresh(self) -> None:
        self.refresh_todos()

    def action_cycle_theme(self) -> None:
        cycle_theme = getattr(self.app, "cycle_theme", None)
        if cycle_theme is None:
            return
        theme_name = cycle_theme()
        self.query_one("#status", Static).update(f"list  Theme: {theme_name}")

    async def action_copy_selected_content(self) -> None:
        if self.search_active:
            return
        todo = self.selected_todo()
        if todo is None:
            self.query_one("#status", Static).update("list  No note selected")
            return
        self.query_one("#status", Static).update("list  Copying note content")
        try:
            await asyncio.to_thread(copy_text, todo.content)
        except ClipboardError as exc:
            self.query_one("#status", Static).update(f"list  {exc}")
            return
        self.query_one("#status", Static).update("list  Copied note content")

    async def action_paste_clipboard_note(self) -> None:
        if self.search_active:
            return
        self.query_one("#status", Static).update("list  Reading clipboard")
        try:
            content = await asyncio.to_thread(paste_text)
        except ClipboardError as exc:
            self.query_one("#status", Static).update(f"list  {exc}")
            return
        if content == "":
            self.query_one("#status", Static).update("list  Clipboard is empty")
            return
        self.app.push_screen(
            EditorScreen(self.service, initial_content=content),
            self._after_editor,
        )

    async def action_execute_selected_content(self) -> None:
        if self.search_active:
            return
        todo = self.selected_todo()
        if todo is None:
            self.query_one("#status", Static).update("list  No note selected")
            return

        def on_confirm(confirmed: bool | None) -> None:
            if confirmed:
                self.run_worker(self._execute_note_content(todo), exclusive=True)

        self.app.push_screen(ConfirmExecuteModal(todo.title), on_confirm)

    async def _execute_note_content(self, todo: Todo) -> None:
        self.query_one("#status", Static).update("list  Executing note content")
        returncode: int | None = None
        error: OSError | None = None
        with self.app.suspend():
            print(f"NoTUI executing note: {todo.title}")
            print()
            try:
                returncode = run_note_script(todo.content)
            except OSError as exc:
                error = exc
                print(f"NoTUI could not execute note: {exc}")
            print()
            with suppress(EOFError):
                input("Press Enter to return to NoTUI")
        if error is not None:
            self.query_one("#status", Static).update(f"list  Script failed: {error}")
            return
        self.query_one("#status", Static).update(f"list  Script exited {returncode}")
