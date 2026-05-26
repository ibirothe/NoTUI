# NoTUI

`NoTUI` is a keyboard-first local note TUI for Arch. It uses
Textual for the interface and SQLite for local persistence.

<img width="778" height="439" alt="image" src="https://github.com/user-attachments/assets/3f18caac-98b2-4e95-be0b-b3406b0a9a93" />
<img width="776" height="435" alt="image" src="https://github.com/user-attachments/assets/7c0f7134-71e8-447f-8822-a43d7b736a36" />


## Install

```bash
pipx install .
notui
```

## Commands

```bash
notui
notui --db /path/to/notes.sqlite
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
n             new note
enter         open selected note
e             edit selected note
d             delete selected note
/             search
escape        clear search or cancel edit
j/down        move down
k/up          move up
g             first note
G             last note
r             refresh
ctrl+x        run selected note content as a shell script
ctrl+c        copy selected note content
ctrl+v        paste clipboard into a new note draft
ctrl+s        save in editor
ctrl+t        cycle theme
```

## Config

Default config path: `$XDG_CONFIG_HOME/notui/config.toml`, falling back to
`~/.config/notui/config.toml`.
The selected theme is saved in `$XDG_STATE_HOME/notui/theme.toml` and restored
on the next launch.

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
