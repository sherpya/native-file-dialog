"""
native_file_dialog: native open/save file dialogs (single and multiple selection).

Uses Qt or GTK on Linux (via XDG_CURRENT_DESKTOP), PyWin32 on Windows,
osascript or PyObjC on macOS, with tkinter fallback.
"""

from __future__ import annotations

import importlib
import os
import sys
from functools import cache
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import TypeAlias, List, Tuple, Literal

    PathLike: TypeAlias = str | os.PathLike
    FilterSpec: TypeAlias = List[Tuple[str, str]]
    Backend: TypeAlias = Literal['tk', 'qt', 'gtk', 'pyobjc', 'osascript']

__all__ = ['open_file', 'open_multiple', 'save_file', 'open_directory']

package = 'native_file_dialog.backends'


@cache
def get_backend():
    """Resolve and cache the backend for the current platform."""
    if sys.platform == 'win32':
        return importlib.import_module('.win32', package=package)

    if sys.platform == 'darwin':
        try:
            return importlib.import_module('.pyobjc', package=package)
        except ImportError:
            return importlib.import_module('.osascript', package=package)

    # Linux: choose order by XDG_CURRENT_DESKTOP
    xdg = os.environ.get('XDG_CURRENT_DESKTOP', '').upper()
    if 'KDE' in xdg:
        order = ('.qt', '.gtk')
    elif 'GNOME' in xdg or 'XFCE' in xdg or 'MATE' in xdg:
        order = ('.gtk', '.qt')
    else:
        order = ('.qt', '.gtk')

    for name in order:
        try:
            return importlib.import_module(name, package=package)
        except ImportError:
            continue

    return importlib.import_module('.tk', package=package)


def resolve_backend(override: Backend | None = None):
    """
    Resolve backend: if backend_override is 'gtk', 'qt', 'pyobjc', 'osascript', 'tk',
    use that backend (gtk/qt only on Linux; pyobj/osascript on macOS, tk on any platform).
    Otherwise, autodetect.
    """
    if not override:
        return get_backend()

    if override == 'tk':
        return importlib.import_module('.tk', package=package)

    if sys.platform == 'linux':
        if override == 'gtk':
            return importlib.import_module('.gtk', package=package)
        elif override == 'qt':
            return importlib.import_module('.qt', package=package)

    if sys.platform == 'darwin':
        if override == 'pyobjc':
            return importlib.import_module('.pyobjc', package=package)
        elif override == 'osascript':
            return importlib.import_module('.osascript', package=package)

    raise Exception(f'Invalid Backend {override} for platform {sys.platform}')


def open_file(title: str | None = None, initialdir: PathLike | None = None, filters: FilterSpec | None = None,
              backend: Backend | None = None) -> str | None:
    """
    Open a file selection dialog for a single file.

    :param title: Dialog title (default backend-specific).
    :param initialdir: Initial directory.
    :param filters: List of (description, pattern) tuples, e.g. [('Python', '*.py')].
    :param backend: Force backend: 'gtk', 'qt' (Linux), 'pyobjc', 'osascript' (macOS), or 'tk' (any platform).
    :return: Selected file path or None if cancelled.
    """
    backend_module = resolve_backend(backend)
    if initialdir is not None:
        initialdir = os.fspath(initialdir)
    return backend_module.open_file(title=title or '', initialdir=initialdir or '.', filters=filters)


def open_multiple(title: str | None = None, initialdir: PathLike | None = None, filters: FilterSpec | None = None,
                  backend: Backend | None = None) -> List[str]:
    """
    Open a file selection dialog for multiple files.

    :param title: Dialog title.
    :param initialdir: Initial directory.
    :param filters: Same as open_file.
    :param backend: Force backend: 'gtk', 'qt' (Linux), 'pyobjc', 'osascript' (macOS), or 'tk' (any platform).
    :return: List of selected paths (empty if cancelled).
    """
    backend_module = resolve_backend(backend)

    if initialdir is not None:
        initialdir = os.fspath(initialdir)

    return backend_module.open_multiple(title=title or '', initialdir=initialdir or '.', filters=filters)


def save_file(title: str | None = None, initialdir: PathLike | None = None,
              backend: Backend | None = None, ) -> str | None:
    """
    Open a save file dialog.

    :param title: Dialog title.
    :param initialdir: Initial directory.
    :param backend: Force backend: 'gtk', 'qt' (Linux), or 'tk' (any platform).
    :return: Selected path or None if cancelled.
    """
    backend_module = resolve_backend(backend)
    if initialdir is not None:
        initialdir = os.fspath(initialdir)

    return backend_module.save_file(title=title or '', initialdir=initialdir or '.')


def open_directory(title: str | None = None, initialdir: PathLike | None = None,
                   backend: Backend | None = None) -> str | None:
    """
    Open a directory selection dialog.

    :param title: Dialog title.
    :param initialdir: Initial directory.
    :param backend: Force backend: 'gtk', 'qt' (Linux), 'pyobjc', 'osascript' (macOS), or 'tk' (any platform).
    :return: Selected directory path or None if cancelled.
    """
    backend_module = resolve_backend(backend)
    if initialdir is not None:
        initialdir = os.fspath(initialdir)
    return backend_module.open_directory(title=title or '', initialdir=initialdir or '.')
