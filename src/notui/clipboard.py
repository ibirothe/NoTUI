from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass

from notui.exceptions import NoTUIError


class ClipboardError(NoTUIError):
    """Raised when clipboard access fails."""


@dataclass(frozen=True, slots=True)
class ClipboardBackend:
    copy_command: tuple[str, ...]
    paste_command: tuple[str, ...]
    copy_exits: bool = True


BACKENDS = (
    ClipboardBackend(("wl-copy",), ("wl-paste",)),
    ClipboardBackend(
        ("xclip", "-selection", "clipboard"),
        ("xclip", "-selection", "clipboard", "-o"),
        copy_exits=False,
    ),
    ClipboardBackend(
        ("xsel", "--clipboard", "--input"),
        ("xsel", "--clipboard", "--output"),
        copy_exits=False,
    ),
    ClipboardBackend(("pbcopy",), ("pbpaste",)),
)

PASTE_TIMEOUT_SECONDS = 1
COPY_TIMEOUT_SECONDS = 1


def _available_backends() -> list[ClipboardBackend]:
    return [
        backend
        for backend in BACKENDS
        if shutil.which(backend.copy_command[0]) and shutil.which(backend.paste_command[0])
    ]


def copy_text(text: str) -> None:
    for backend in _available_backends():
        try:
            if backend.copy_exits:
                subprocess.run(
                    backend.copy_command,
                    input=text,
                    text=True,
                    capture_output=True,
                    check=True,
                    timeout=COPY_TIMEOUT_SECONDS,
                )
            else:
                process = subprocess.Popen(
                    backend.copy_command,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    start_new_session=True,
                )
                if process.stdin is None:
                    continue
                process.stdin.write(text)
                process.stdin.close()
            return
        except (OSError, BrokenPipeError, subprocess.SubprocessError):
            continue
    raise ClipboardError("Could not copy to clipboard")


def paste_text() -> str:
    for backend in _available_backends():
        try:
            result = subprocess.run(
                backend.paste_command,
                text=True,
                capture_output=True,
                check=True,
                timeout=PASTE_TIMEOUT_SECONDS,
            )
            return result.stdout
        except (OSError, subprocess.SubprocessError):
            continue
    raise ClipboardError("Could not read clipboard")
