from __future__ import annotations

import sqlite3

import pytest
from textual.widgets import TextArea

from notui.app import NoTUIApp
from notui.config import load_saved_theme_name
from notui.migrations import migrate
from notui.models import Todo
from notui.repository import TodoRepository
from notui.services import TodoService
from notui.tui.theme import RUNTIME_THEME_SOURCE
from notui.tui.widgets import NOTUI_LOGO


@pytest.mark.asyncio
async def test_app_starts_and_empty_state_renders() -> None:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    migrate(connection)
    app = NoTUIApp(service=TodoService(TodoRepository(connection)))

    async with app.run_test() as pilot:
        assert NOTUI_LOGO in str(pilot.app.screen.query_one("#detail-logo").render())


@pytest.mark.asyncio
async def test_ctrl_t_cycles_and_saves_theme(tmp_path) -> None:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    migrate(connection)
    app = NoTUIApp(service=TodoService(TodoRepository(connection)), state_dir=tmp_path)

    async with app.run_test() as pilot:
        assert app.active_theme_name == "dark"
        await pilot.press("ctrl+t")
        assert app.active_theme_name == "light"
        assert "#f4f4f4" in app.stylesheet.source[RUNTIME_THEME_SOURCE].content
        assert "Theme: light" in str(pilot.app.screen.query_one("#status").render())
        assert load_saved_theme_name(tmp_path) == "light"

    next_app = NoTUIApp(service=TodoService(TodoRepository(connection)), state_dir=tmp_path)

    assert next_app.active_theme_name == "light"


@pytest.mark.asyncio
async def test_search_mode_is_visible() -> None:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    migrate(connection)
    app = NoTUIApp(service=TodoService(TodoRepository(connection)))

    async with app.run_test() as pilot:
        assert pilot.app.screen.query_one("#searchbar").display is False
        assert "FILTER" in str(pilot.app.screen.query_one("#search-label").render())
        await pilot.press("/")
        assert pilot.app.screen.query_one("#searchbar").display is True
        assert "SEARCH" in str(pilot.app.screen.query_one("#search-label").render())
        assert "typing filters" in str(pilot.app.screen.query_one("#status").render())
        await pilot.press("escape")
        assert pilot.app.screen.query_one("#searchbar").display is False


@pytest.mark.asyncio
async def test_existing_notes_do_not_open_until_selected() -> None:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    migrate(connection)
    service = TodoService(TodoRepository(connection))
    service.create("First note", "Body")
    app = NoTUIApp(service=service)

    async with app.run_test() as pilot:
        assert NOTUI_LOGO in str(pilot.app.screen.query_one("#detail-logo").render())
        assert str(pilot.app.screen.query_one("#detail-title").render()) == ""
        await pilot.press("down")
        assert "First note" in str(pilot.app.screen.query_one("#detail-title").render())


@pytest.mark.asyncio
async def test_note_metadata_uses_muted_detail_widgets() -> None:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    migrate(connection)
    service = TodoService(TodoRepository(connection))
    service.create("First note", "Body")
    app = NoTUIApp(service=service)

    async with app.run_test() as pilot:
        await pilot.press("down")
        created = pilot.app.screen.query_one("#detail-created")
        changed = pilot.app.screen.query_one("#detail-changed")
        assert "Created:" in str(created.render())
        assert "Changed:" in str(changed.render())
        assert created.has_class("muted")
        assert changed.has_class("muted")


@pytest.mark.asyncio
async def test_note_metadata_uses_human_readable_dates() -> None:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    migrate(connection)
    repository = TodoRepository(connection)
    repository.insert(
        Todo(
            uuid="note-id",
            title="First note",
            content="Body",
            created_at="2026-05-25T13:45:12.123456Z",
            last_change="2026-05-25T15:45:12+02:00",
        )
    )
    app = NoTUIApp(service=TodoService(repository))

    async with app.run_test() as pilot:
        await pilot.press("down")
        created = str(pilot.app.screen.query_one("#detail-created").render())
        changed = str(pilot.app.screen.query_one("#detail-changed").render())
        assert "Created: May 25, 2026 at" in created
        assert "Changed: May 25, 2026 at" in changed
        assert "T13:45:12" not in created
        assert "T15:45:12" not in changed


@pytest.mark.asyncio
async def test_ctrl_c_copies_selected_note_content(monkeypatch: pytest.MonkeyPatch) -> None:
    copied: list[str] = []
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    migrate(connection)
    service = TodoService(TodoRepository(connection))
    service.create("First note", "Body")
    app = NoTUIApp(service=service)
    monkeypatch.setattr("notui.tui.screens.copy_text", copied.append)

    async with app.run_test() as pilot:
        await pilot.press("down")
        await pilot.press("ctrl+c")
        assert copied == ["Body"]
        assert "Copied note content" in str(pilot.app.screen.query_one("#status").render())


@pytest.mark.asyncio
async def test_ctrl_v_opens_editor_with_clipboard_content(monkeypatch: pytest.MonkeyPatch) -> None:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    migrate(connection)
    app = NoTUIApp(service=TodoService(TodoRepository(connection)))
    monkeypatch.setattr("notui.tui.screens.paste_text", lambda: "Clipboard body")

    async with app.run_test() as pilot:
        await pilot.press("ctrl+v")
        await pilot.pause()
        assert pilot.app.screen.query_one("#editor-content", TextArea).text == "Clipboard body"


@pytest.mark.asyncio
async def test_ctrl_v_ignores_empty_clipboard(monkeypatch: pytest.MonkeyPatch) -> None:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    migrate(connection)
    app = NoTUIApp(service=TodoService(TodoRepository(connection)))
    monkeypatch.setattr("notui.tui.screens.paste_text", lambda: "")

    async with app.run_test() as pilot:
        await pilot.press("ctrl+v")
        await pilot.pause()
        assert "Clipboard is empty" in str(pilot.app.screen.query_one("#status").render())


@pytest.mark.asyncio
async def test_q_quits_app() -> None:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    migrate(connection)
    app = NoTUIApp(service=TodoService(TodoRepository(connection)))

    async with app.run_test() as pilot:
        await pilot.press("q")
        await pilot.pause()
        assert app.is_running is False
