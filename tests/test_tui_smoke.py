from __future__ import annotations

import sqlite3

import pytest

from notui.app import NoTUIApp
from notui.migrations import migrate
from notui.repository import TodoRepository
from notui.services import TodoService
from notui.tui.theme import RUNTIME_THEME_SOURCE


@pytest.mark.asyncio
async def test_app_starts_and_empty_state_renders() -> None:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    migrate(connection)
    app = NoTUIApp(service=TodoService(TodoRepository(connection)))

    async with app.run_test() as pilot:
        assert "No todos yet" in str(pilot.app.screen.query_one("#detail").render())


@pytest.mark.asyncio
async def test_ctrl_t_cycles_theme() -> None:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    migrate(connection)
    app = NoTUIApp(service=TodoService(TodoRepository(connection)))

    async with app.run_test() as pilot:
        assert app.active_theme_name == "dark"
        await pilot.press("ctrl+t")
        assert app.active_theme_name == "light"
        assert "#f4f4f4" in app.stylesheet.source[RUNTIME_THEME_SOURCE].content
        assert "Theme: light" in str(pilot.app.screen.query_one("#status").render())


@pytest.mark.asyncio
async def test_search_mode_is_visible() -> None:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    migrate(connection)
    app = NoTUIApp(service=TodoService(TodoRepository(connection)))

    async with app.run_test() as pilot:
        assert "FILTER" in str(pilot.app.screen.query_one("#search-label").render())
        await pilot.press("/")
        assert "SEARCH" in str(pilot.app.screen.query_one("#search-label").render())
        assert "typing filters" in str(pilot.app.screen.query_one("#status").render())


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
