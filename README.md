# NoTUI

`NoTUI` is a keyboard-first local note TUI for Arch. It uses
Textual for the interface and SQLite for local persistence.

## Install

```bash
pipx install .
notui
```

Development:

```bash
uv run pytest
uv run ruff check
uv run ruff format --check
```

## Commands

```bash
notui
notui --db /path/to/todos.sqlite
notui --config /path/to/config.toml
notui --version
notui doctor
```

The default database path is `$XDG_DATA_HOME/notui/notui.sqlite`, falling
back to `~/.local/share/notui/notui.sqlite`.

## Keyboard

```text
q             quit
?             help
n             new todo
enter         open selected todo
e             edit selected todo
d             delete selected todo
/             search
escape        clear search or cancel edit
j/down        move down
k/up          move up
g             first todo
G             last todo
r             refresh
ctrl+s        save in editor
ctrl+t        cycle theme
```

Optional Hyprland binding snippet:

```conf
bind = SUPER, N, exec, alacritty --class notui --title NoTUI -e notui
```

## Config

Default config path: `$XDG_CONFIG_HOME/notui/config.toml`, falling back to
`~/.config/notui/config.toml`.

```toml
[database]
path = ""

[theme]
background = "#0b0b0b"
panel_background = "#151515"
text = "#e8e8e8"
secondary_text = "#8a8a8a"

[ui]
confirm_delete = true
autosave_on_blur = false
```
