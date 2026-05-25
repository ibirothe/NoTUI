from __future__ import annotations

from dataclasses import dataclass

from notui.config import Theme


@dataclass(frozen=True, slots=True)
class NamedTheme:
    name: str
    theme: Theme


BUILTIN_THEMES = (
    NamedTheme("dark", Theme()),
    NamedTheme(
        "light",
        Theme(
            background="#f4f4f4",
            panel_background="#ffffff",
            text="#111111",
            secondary_text="#666666",
        ),
    ),
    NamedTheme(
        "contrast",
        Theme(
            background="#000000",
            panel_background="#111111",
            text="#ffffff",
            secondary_text="#bdbdbd",
        ),
    ),
    NamedTheme(
        "terminal",
        Theme(
            background="#101010",
            panel_background="#1c1c1c",
            text="#d7d7d7",
            secondary_text="#9e9e9e",
        ),
    ),
)

RUNTIME_THEME_SOURCE = ("notui", "runtime-theme")


def theme_cycle(start_theme: Theme, custom_theme: bool) -> list[NamedTheme]:
    if custom_theme:
        return [NamedTheme("custom", start_theme), *BUILTIN_THEMES]
    return list(BUILTIN_THEMES)


def theme_css(theme: Theme) -> str:
    return f"""
$background: {theme.background};
$panel-background: {theme.panel_background};
$text: {theme.text};
$secondary-text: {theme.secondary_text};
"""
