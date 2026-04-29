from __future__ import annotations

import builtins
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .. import FilterSpec

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


# Try GTK4 first, fall back to GTK3 only if GTK4 cannot be imported.
try:
    from native_file_dialog_gtk import (
        open_file as _open_file,
        open_multiple as _open_multiple,
        save_file as _save_file,
        open_directory as _open_directory,
    )
    _ensure_gtk_major(4)
except ImportError:
    _ensure_gtk_major(3)
    from native_file_dialog_gtk3 import (
        open_file as _open_file,
        open_multiple as _open_multiple,
        save_file as _save_file,
        open_directory as _open_directory,
    )


def filter_to_gtk_string(filters: FilterSpec | None = None) -> List[str]:
    """GTK format: list of 'Description | pattern1 pattern2'."""
    if not filters:
        return []
    # GTK uses spaces to separate multiple patterns; normalize semicolons
    return [f'{desc} | {pattern.replace(";", " ")}' for desc, pattern in filters]


def open_file(title: str | None = None, initialdir: str | None = None,
              filters: FilterSpec | None = None, multiple: bool = False) -> List[str] | None:
    if multiple:
        result = _open_multiple(title or '', initialdir or '', filter_to_gtk_string(filters))
        return result if result else None
    path = _open_file(title or '', initialdir or '', filter_to_gtk_string(filters))
    return [path] if path is not None else None


def save_file(title: str | None = None, initialdir: str | None = None,
              filters: FilterSpec | None = None, default_name: str | None = None) -> str | None:
    result = _save_file(title or '', initialdir or '', filter_to_gtk_string(filters), default_name or '')
    return result if result is not None else None


def open_directory(title: str | None = None, initialdir: str | None = None) -> str | None:
    result = _open_directory(title or '', initialdir or '')
    return result if result is not None else None
