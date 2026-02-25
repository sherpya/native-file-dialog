from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import List
    from .. import FilterSpec

from .._native_gtk import (
    open_file as _open_file,
    open_multiple as _open_multiple,
    save_file as _save_file,
    open_directory as _open_directory,
)


def filter_to_gtk_string(filters: FilterSpec | None = None) -> List[str]:
    """GTK format: list of 'Description | pattern1 pattern2'."""
    if not filters:
        return []
    return [f'{desc} | {pattern}' for desc, pattern in filters]


def open_file(title: str | None = None, initialdir: str | None = None,
              filters: FilterSpec | None = None) -> str | None:
    result = _open_file(title or '', initialdir or '', filter_to_gtk_string(filters))
    return result if result is not None else None


def open_multiple(title: str | None = None, initialdir: str | None = None,
                  filters: FilterSpec | None = None) -> List[str]:
    return _open_multiple(title or '', initialdir or '', filter_to_gtk_string(filters))


def save_file(title: str | None = None, initialdir: str | None = None) -> str | None:
    result = _save_file(title or '', initialdir or '')
    return result if result is not None else None


def open_directory(title: str | None = None, initialdir: str | None = None) -> str | None:
    result = _open_directory(title or '', initialdir or '')
    return result if result is not None else None
