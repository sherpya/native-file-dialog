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


def open_file(title: str | None = None, initialdir: str | None = None,
              filters: FilterSpec | None = None, multiple: bool = False) -> List[str] | None:
    get_root()
    if multiple:
        paths = filedialog.askopenfilenames(title=title, initialdir=initialdir, filetypes=filters or [])
        return list(paths) if paths else None
    path = filedialog.askopenfilename(title=title, initialdir=initialdir, filetypes=filters or [])
    return [path] if path else None


def save_file(title: str | None = None, initialdir: str | None = None,
              filters: FilterSpec | None = None) -> str | None:
    get_root()
    return filedialog.asksaveasfilename(title=title, initialdir=initialdir, filetypes=filters or []) or None


def open_directory(title: str | None = None, initialdir: str | None = None) -> str | None:
    get_root()
    return filedialog.askdirectory(title=title, initialdir=initialdir) or None
