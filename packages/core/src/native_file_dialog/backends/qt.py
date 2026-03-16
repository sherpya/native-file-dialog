from __future__ import annotations

import os
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .. import FilterSpec

from native_file_dialog_qt import (
    open_file as _open_file,
    open_multiple as _open_multiple,
    save_file as _save_file,
    open_directory as _open_directory,
)


def filter_to_qt_string(filters: FilterSpec | None = None) -> str:
    """Qt format: 'Description (*.a *.b);;Other (*.c)' (;; between entries, space between patterns)."""
    if not filters:
        return ''
    return ';;'.join((f'{desc} ({pattern})' for desc, pattern in filters))


def open_file(title: str | None = None, initialdir: str | None = None,
              filters: FilterSpec | None = None, multiple: bool = False) -> List[str] | None:
    if multiple:
        result = _open_multiple(title or '', initialdir or '', filter_to_qt_string(filters))
        return result if result else None
    path = _open_file(title or '', initialdir or '', filter_to_qt_string(filters))
    return [path] if path is not None else None


def save_file(title: str | None = None, initialdir: str | None = None,
              filters: FilterSpec | None = None) -> str | None:
    result = _save_file(title or '', os.fspath(initialdir) if initialdir else '', filter_to_qt_string(filters))
    return result if result is not None else None


def open_directory(title: str | None = None, initialdir: str | None = None) -> str | None:
    result = _open_directory(title or '', os.fspath(initialdir) if initialdir else '')
    return result if result is not None else None
