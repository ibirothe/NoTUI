from __future__ import annotations

import subprocess

import pytest

from notui.clipboard import ClipboardError, copy_text, paste_text


def test_copy_text_uses_available_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    commands: list[tuple[str, ...]] = []

    def fake_which(command: str) -> str | None:
        return f"/usr/bin/{command}" if command == "wl-copy" or command == "wl-paste" else None

    def fake_run(
        command: tuple[str, ...],
        input: str | None = None,
        text: bool = False,
        capture_output: bool = False,
        check: bool = False,
        timeout: int | None = None,
    ) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        assert input == "note body"
        assert text is True
        assert capture_output is True
        assert check is True
        assert timeout == 1
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr("notui.clipboard.shutil.which", fake_which)
    monkeypatch.setattr("notui.clipboard.subprocess.run", fake_run)

    copy_text("note body")

    assert commands == [("wl-copy",)]


def test_copy_text_does_not_wait_for_long_lived_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    writes: list[str] = []

    class FakeStdin:
        def write(self, text: str) -> None:
            writes.append(text)

        def close(self) -> None:
            writes.append("closed")

    class FakeProcess:
        stdin = FakeStdin()

    def fake_which(command: str) -> str | None:
        return f"/usr/bin/{command}" if command == "xclip" else None

    def fake_popen(
        command: tuple[str, ...],
        stdin: int,
        stdout: int,
        stderr: int,
        text: bool,
        start_new_session: bool,
    ) -> FakeProcess:
        assert command == ("xclip", "-selection", "clipboard")
        assert stdin == subprocess.PIPE
        assert stdout == subprocess.DEVNULL
        assert stderr == subprocess.DEVNULL
        assert text is True
        assert start_new_session is True
        return FakeProcess()

    monkeypatch.setattr("notui.clipboard.shutil.which", fake_which)
    monkeypatch.setattr("notui.clipboard.subprocess.Popen", fake_popen)

    copy_text("note body")

    assert writes == ["note body", "closed"]


def test_paste_text_returns_available_backend_output(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_which(command: str) -> str | None:
        return f"/usr/bin/{command}" if command == "xclip" else None

    def fake_run(
        command: tuple[str, ...],
        text: bool = False,
        capture_output: bool = False,
        check: bool = False,
        timeout: int | None = None,
    ) -> subprocess.CompletedProcess[str]:
        assert command == ("xclip", "-selection", "clipboard", "-o")
        assert text is True
        assert capture_output is True
        assert check is True
        assert timeout == 1
        return subprocess.CompletedProcess(command, 0, "clipboard text", "")

    monkeypatch.setattr("notui.clipboard.shutil.which", fake_which)
    monkeypatch.setattr("notui.clipboard.subprocess.run", fake_run)

    assert paste_text() == "clipboard text"


def test_clipboard_errors_when_no_backend_exists(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("notui.clipboard.shutil.which", lambda command: None)

    with pytest.raises(ClipboardError, match="Could not copy"):
        copy_text("body")

    with pytest.raises(ClipboardError, match="Could not read"):
        paste_text()
