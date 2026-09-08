from __future__ import annotations

import os
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .. import EventPump, FilterSpec

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
    # Qt uses spaces to separate multiple patterns; normalize semicolons
    return ';;'.join((f'{desc} ({pattern.replace(";", " ")})' for desc, pattern in filters))


def open_file(title: str | None = None, initialdir: str | None = None,
              filters: FilterSpec | None = None, multiple: bool = False, *, event_pump: EventPump | None = None) -> List[str] | None:
    if multiple:
        result = _open_multiple(title or '', initialdir or '', filter_to_qt_string(filters), *(() if event_pump is None else (event_pump,)))
        return result if result else None
    path = _open_file(title or '', initialdir or '', filter_to_qt_string(filters), *(() if event_pump is None else (event_pump,)))
    return [path] if path is not None else None


def save_file(title: str | None = None, initialdir: str | None = None,
              filters: FilterSpec | None = None, default_name: str | None = None, *, event_pump: EventPump | None = None) -> str | None:
    result = _save_file(title or '', os.fspath(initialdir) if initialdir else '', filter_to_qt_string(filters), default_name or '', *(() if event_pump is None else (event_pump,)))
    return result if result is not None else None


def open_directory(title: str | None = None, initialdir: str | None = None, *,
                   event_pump: EventPump | None = None) -> str | None:
    result = _open_directory(title or '', os.fspath(initialdir) if initialdir else '', *(() if event_pump is None else (event_pump,)))
    return result if result is not None else None
