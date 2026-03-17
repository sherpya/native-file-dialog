"""
    macOS file dialog backend via osascript (AppleScript NSOpenPanel / NSSavePanel).
"""

from __future__ import annotations

import logging
import os
import subprocess
from typing import List

log = logging.getLogger(__name__)


def run_applescript(script: str) -> str | None:
    """Run AppleScript and return stdout, or None if the user cancelled."""
    try:
        return subprocess.check_output(['osascript', '-e', script], text=True, stderr=subprocess.PIPE).strip()
    except subprocess.CalledProcessError as e:
        stderr = (e.stderr or '').strip()
        if '-128' in stderr:  # User canceled. (-128)
            return None
        log.warning('osascript failed (rc=%d): %s', e.returncode, stderr)
        return None


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
        opts.append(f'default location (POSIX file "{_escape_applescript(os.path.abspath(initialdir))}")')

    if multiple:
        out = run_applescript(OPEN_MULTIPLE_SCRIPT.format(' '.join(opts)))
        if not out:
            return None
        paths = [p.strip() for p in out.split('\n') if p.strip()]
        return paths if paths else None

    script = 'POSIX path of (choose file' + (' ' + ' '.join(opts) if opts else '') + ')'
    out = run_applescript(script)
    return [out] if out else None


def save_file(title: str | None = None, initialdir: str | None = None,
              filters=None) -> str | None:
    opts = []

    if title:
        opts.append(f'with prompt "{_escape_applescript(title)}"')

    if initialdir:
        opts.append(f'default location (POSIX file "{_escape_applescript(os.path.abspath(initialdir))}")')

    script = 'POSIX path of (choose file name' + (' ' + ' '.join(opts) if opts else '') + ')'
    return run_applescript(script) or None


def open_directory(title: str | None = None, initialdir: str | None = None) -> str | None:
    opts = []

    if title:
        opts.append(f'with prompt "{_escape_applescript(title)}"')

    if initialdir:
        opts.append(f'default location (POSIX file "{_escape_applescript(os.path.abspath(initialdir))}")')

    script = 'POSIX path of (choose folder' + (' ' + ' '.join(opts) if opts else '') + ')'
    return run_applescript(script) or None
