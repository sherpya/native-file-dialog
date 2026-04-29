"""
native_file_dialog: native open/save file dialogs (single and multiple selection).

Uses Qt or GTK on Linux (via XDG_CURRENT_DESKTOP), ctypes on Windows,
PyObjC on macOS, with tkinter fallback.
"""

from __future__ import annotations

import importlib
import os
import sys
import builtins
from functools import cache
from typing import List, Literal, Tuple, TypeAlias

PathLike: TypeAlias = str | os.PathLike[str]
FilterSpec: TypeAlias = List[Tuple[str, str]]
Backend: TypeAlias = Literal['tk', 'qt', 'gtk', 'gtk3', 'pyobjc']

__all__ = ['open_file', 'save_file', 'open_directory', 'FilterSpec', 'Backend']

package = 'native_file_dialog.backends'

_GTK_MARKER = '_native_file_dialog_gtk_major'
_GTK_MIX_ERROR = (
    'Cannot use GTK{requested} after GTK{active} in the same Python process; '
    'choose one GTK backend per process or run the other backend in a subprocess.'
)


def _active_gtk_major() -> int | None:
    active = getattr(builtins, _GTK_MARKER, None)
    return active if active in (3, 4) else None


def _ensure_gtk_major(requested: int) -> None:
    active = _active_gtk_major()
    if active is not None and active != requested:
        raise RuntimeError(_GTK_MIX_ERROR.format(requested=requested, active=active))
    setattr(builtins, _GTK_MARKER, requested)


def _import_gtk3_backend():
    _ensure_gtk_major(3)
    return importlib.import_module('.gtk3', package=package)


@cache
def get_backend():
    """Resolve and cache the backend for the current platform."""
    if sys.platform == 'win32':
        return importlib.import_module('.win32', package=package)

    if sys.platform == 'darwin':
        try:
            return importlib.import_module('.pyobjc', package=package)
        except ImportError:
            return importlib.import_module('.tk', package=package)

    # Linux: choose order by XDG_CURRENT_DESKTOP
    xdg = os.environ.get('XDG_CURRENT_DESKTOP', '').upper()
    if 'KDE' in xdg:
        order = ('.qt', '.gtk')
    elif 'GNOME' in xdg or 'XFCE' in xdg or 'MATE' in xdg:
        order = ('.gtk', '.qt')
    else:
        order = ('.qt', '.gtk')

    if _active_gtk_major() == 3:
        order = tuple('.gtk3' if name == '.gtk' else name for name in order)

    for name in order:
        try:
            return importlib.import_module(name, package=package)
        except ImportError:
            continue

    return importlib.import_module('.tk', package=package)


def resolve_backend(override: Backend | None = None):
    """
    Resolve backend: if override is 'gtk', 'gtk3', 'qt', 'pyobjc', 'tk',
    use that backend. Otherwise, autodetect.
    """
    if not override:
        return get_backend()

    if override == 'tk':
        return importlib.import_module('.tk', package=package)

    if sys.platform == 'linux':
        if override == 'gtk':
            _ensure_gtk_major(4)
            return importlib.import_module('.gtk', package=package)
        elif override == 'gtk3':
            return _import_gtk3_backend()
        elif override == 'qt':
            return importlib.import_module('.qt', package=package)

    if sys.platform == 'darwin':
        if override == 'pyobjc':
            return importlib.import_module('.pyobjc', package=package)

    raise Exception(f'Invalid Backend {override} for platform {sys.platform}')


def open_file(title: str | None = None, initialdir: PathLike | None = None, filters: FilterSpec | None = None,
              multiple: bool = False, backend: Backend | None = None) -> List[str] | None:
    """
    Open a file selection dialog.

    :param title: Dialog title (default backend-specific).
    :param initialdir: Initial directory.
    :param filters: List of (description, pattern) tuples, e.g. [('Python', '*.py')].
    :param multiple: If True, allow selecting multiple files.
    :param backend: Force backend: 'gtk', 'gtk3', 'qt' (Linux), 'pyobjc' (macOS), or 'tk' (any platform).
    :return: List of selected paths, or None if cancelled. Single selection returns [path].
    """
    backend_module = resolve_backend(backend)
    if initialdir is not None:
        initialdir = os.fspath(initialdir)
    return backend_module.open_file(title=title or '', initialdir=initialdir or '.', filters=filters, multiple=multiple)


def save_file(title: str | None = None, initialdir: PathLike | None = None, filters: FilterSpec | None = None,
              default_name: str | None = None, backend: Backend | None = None) -> str | None:
    """
    Open a save file dialog.

    :param title: Dialog title.
    :param initialdir: Initial directory.
    :param filters: List of (description, pattern) tuples, e.g. [('PDF files', '*.pdf')].
    :param default_name: Pre-filled file name suggestion.
    :param backend: Force backend: 'gtk', 'gtk3', 'qt' (Linux), 'pyobjc' (macOS), or 'tk' (any platform).
    :return: Selected path or None if cancelled.
    """
    backend_module = resolve_backend(backend)
    if initialdir is not None:
        initialdir = os.fspath(initialdir)
    return backend_module.save_file(title=title or '', initialdir=initialdir or '.', filters=filters,
                                    default_name=default_name)


def open_directory(title: str | None = None, initialdir: PathLike | None = None,
                   backend: Backend | None = None) -> str | None:
    """
    Open a directory selection dialog.

    :param title: Dialog title.
    :param initialdir: Initial directory.
    :param backend: Force backend: 'gtk', 'gtk3', 'qt' (Linux), 'pyobjc' (macOS), or 'tk' (any platform).
    :return: Selected directory path or None if cancelled.
    """
    backend_module = resolve_backend(backend)
    if initialdir is not None:
        initialdir = os.fspath(initialdir)
    return backend_module.open_directory(title=title or '', initialdir=initialdir or '.')
