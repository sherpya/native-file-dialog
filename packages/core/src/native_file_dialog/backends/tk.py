from __future__ import annotations

import tkinter as tk
from functools import cache
from tkinter import filedialog
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .. import FilterSpec


@cache
def get_root() -> tk.Tk:
    root = tk.Tk()
    root.withdraw()
    return root


def _normalize_filters(filters: FilterSpec | None) -> list:
    """Tk uses spaces to separate multiple patterns; normalize semicolons."""
    if not filters:
        return []
    return [(desc, pattern.replace(';', ' ')) for desc, pattern in filters]


def open_file(title: str | None = None, initialdir: str | None = None,
              filters: FilterSpec | None = None, multiple: bool = False) -> List[str] | None:
    get_root()
    ft = _normalize_filters(filters)
    if multiple:
        paths = filedialog.askopenfilenames(title=title, initialdir=initialdir, filetypes=ft)
        return list(paths) if paths else None
    path = filedialog.askopenfilename(title=title, initialdir=initialdir, filetypes=ft)
    return [path] if path else None


def save_file(title: str | None = None, initialdir: str | None = None,
              filters: FilterSpec | None = None, default_name: str | None = None) -> str | None:
    get_root()
    return filedialog.asksaveasfilename(title=title, initialdir=initialdir, filetypes=_normalize_filters(filters),
                                        initialfile=default_name or '') or None


def open_directory(title: str | None = None, initialdir: str | None = None) -> str | None:
    get_root()
    return filedialog.askdirectory(title=title, initialdir=initialdir) or None
