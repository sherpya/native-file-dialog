"""
    macOS file dialog backend via osascript (AppleScript NSOpenPanel / NSSavePanel).
"""

from __future__ import annotations

import subprocess
from subprocess import SubprocessError
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import List


def run_applescript(script: str) -> str:
    """Run AppleScript and return stdout (strip trailing newline)."""
    return subprocess.check_output(['osascript', '-e', script], text=True).strip()


def _escape_applescript(s: str) -> str:
    return s.replace('\\', '\\\\').replace('"', '\\"')


OPEN_MULTIPLE_SCRIPT = """set AppleScript's text item delimiters to ASCII character 10
set L to choose file {}
set pathList to {{}}
repeat with f in L
  set end of pathList to (POSIX path of f)
end repeat
set out to pathList as text
set AppleScript's text item delimiters to ""
return out"""


def open_file(title: str | None = None, initialdir: str | None = None,
              filters=None, multiple: bool = False) -> List[str] | None:
    opts = []

    if multiple:
        opts.append('with multiple selections allowed')

    if title:
        opts.append(f'with prompt "{_escape_applescript(title)}"')

    if initialdir:
        opts.append(f'default location (POSIX file "{_escape_applescript(initialdir)}")')

    if multiple:
        try:
            out = run_applescript(OPEN_MULTIPLE_SCRIPT.format(' '.join(opts)))
            if not out:
                return None
            paths = [p.strip() for p in out.split('\n') if p.strip()]
            return paths if paths else None
        except SubprocessError:
            return None

    script = 'POSIX path of (choose file' + (' ' + ' '.join(opts) if opts else '') + ')'
    try:
        out = run_applescript(script)
        return [out] if out else None
    except SubprocessError:
        return None


def save_file(title: str | None = None, initialdir: str | None = None) -> str | None:
    opts = []

    if title:
        opts.append(f'with prompt "{_escape_applescript(title)}"')

    if initialdir:
        opts.append(f'default location (POSIX file "{_escape_applescript(initialdir)}")')

    script = 'POSIX path of (choose file name' + (' ' + ' '.join(opts) if opts else '') + ')'

    try:
        out = run_applescript(script)
        return out if out else None
    except SubprocessError:
        return None


def open_directory(title: str | None = None, initialdir: str | None = None) -> str | None:
    opts = []

    if title:
        opts.append(f'with prompt "{_escape_applescript(title)}"')

    if initialdir:
        opts.append(f'default location (POSIX file "{_escape_applescript(initialdir)}")')

    script = 'POSIX path of (choose folder' + (' ' + ' '.join(opts) if opts else '') + ')'

    try:
        out = run_applescript(script)
        return out if out else None
    except SubprocessError:
        return None
