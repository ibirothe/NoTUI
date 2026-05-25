from __future__ import annotations

from textual.app import App, ComposeResult

from notui.config import Theme
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
        startup_error: str | None = None,
    ) -> None:
        super().__init__()
        self.service = service
        self.theme_options: list[NamedTheme] = theme_cycle(theme or Theme(), custom_theme)
        self.active_theme_index = 0
        self.startup_error = startup_error

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
        return self.active_theme_name
