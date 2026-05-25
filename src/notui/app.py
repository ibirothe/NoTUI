from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult

from notui.config import Theme, load_saved_theme_name, save_theme_name
from notui.services import TodoService
from notui.tui.screens import ErrorScreen, MainScreen
from notui.tui.theme import RUNTIME_THEME_SOURCE, NamedTheme, theme_css, theme_cycle


class NoTUIApp(App[None]):
    CSS_PATH = "tui/app.tcss"

    def __init__(
        self,
        service: TodoService | None = None,
        theme: Theme | None = None,
        custom_theme: bool = False,
        state_dir: Path | None = None,
        startup_error: str | None = None,
    ) -> None:
        super().__init__()
        self.service = service
        self.theme_options: list[NamedTheme] = theme_cycle(theme or Theme(), custom_theme)
        self.state_dir = state_dir
        self.active_theme_index = self._initial_theme_index()
        self.startup_error = startup_error

    def _initial_theme_index(self) -> int:
        if self.state_dir is None:
            return 0
        saved_theme_name = load_saved_theme_name(self.state_dir)
        if saved_theme_name is None:
            return 0
        for index, theme in enumerate(self.theme_options):
            if theme.name == saved_theme_name:
                return index
        return 0

    @property
    def active_theme_name(self) -> str:
        return self.theme_options[self.active_theme_index].name

    @property
    def active_theme(self) -> Theme:
        return self.theme_options[self.active_theme_index].theme

    def compose(self) -> ComposeResult:
        yield from ()

    def on_mount(self) -> None:
        self.apply_active_theme()
        if self.startup_error is not None:
            self.push_screen(ErrorScreen(self.startup_error))
        elif self.service is not None:
            self.push_screen(MainScreen(self.service))

    def apply_active_theme(self) -> None:
        self.stylesheet.add_source(
            theme_css(self.active_theme),
            read_from=RUNTIME_THEME_SOURCE,
            tie_breaker=100,
        )

    def cycle_theme(self) -> str:
        self.active_theme_index = (self.active_theme_index + 1) % len(self.theme_options)
        self.apply_active_theme()
        self.refresh_css(animate=False)
        if self.state_dir is not None:
            save_theme_name(self.state_dir, self.active_theme_name)
        return self.active_theme_name

    def action_quit(self) -> None:
        self.exit()
