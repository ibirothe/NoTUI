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
        "cold",
        Theme(
            background="#2c2d2c",
            panel_background="#1a1716",
            text="#508968",
            secondary_text="#496675",
        ),
    ),
    NamedTheme(
        "warm",
        Theme(
            background="#241e26",
            panel_background="#1e1c1d",
            text="#523f3c",
            secondary_text="#915945",
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

Screen {{
  background: $background;
  color: $text;
}}

#topbar {{
  background: $panel-background;
  color: $text;
}}

#top-hints {{
  color: $secondary-text;
}}

.panel {{
  background: $panel-background;
  color: $text;
  border: solid $secondary-text;
}}

.panel-title {{
  color: $secondary-text;
}}

.muted {{
  color: $secondary-text;
}}

.status {{
  background: $panel-background;
  color: $secondary-text;
}}

#searchbar {{
  background: $panel-background;
  color: $text;
  border: solid $secondary-text;
}}

#search-label {{
  color: $secondary-text;
}}

#search {{
  background: $background;
  color: $text;
  border: solid $secondary-text;
}}

ListView {{
  background: $panel-background;
  color: $text;
}}

Input {{
  background: $background;
  color: $text;
  border: solid $secondary-text;
}}

TextArea {{
  background: $background;
  color: $text;
  border: solid $secondary-text;
}}

Button {{
  background: $panel-background;
  color: $text;
  border: solid $secondary-text;
}}

ModalScreen {{
  background: $background;
  color: $text;
}}

.modal {{
  background: $panel-background;
  color: $text;
  border: solid $secondary-text;
}}
"""
