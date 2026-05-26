from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from contextlib import suppress
from pathlib import Path


def default_shell() -> str:
    shell = os.environ.get("SHELL")
    if shell:
        return shell
    return shutil.which("bash") or shutil.which("sh") or "sh"


def run_note_script(content: str, shell: str | None = None) -> int:
    selected_shell = shell or default_shell()
    script_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            prefix="notui-",
            suffix=".sh",
            delete=False,
        ) as handle:
            script_path = Path(handle.name)
            handle.write(content)
        script_path.chmod(0o700)
        return subprocess.run([selected_shell, str(script_path)], check=False).returncode
    finally:
        if script_path is not None:
            with suppress(FileNotFoundError):
                script_path.unlink()
