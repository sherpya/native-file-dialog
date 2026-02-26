from __future__ import annotations

import tkinter as tk
from functools import cache
from tkinter import filedialog
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import List
    from .. import FilterSpec


@cache
def get_root() -> tk.Tk:
    root = tk.Tk()
    root.withdraw()
    return root


def open_file(title: str | None = None, initialdir: str | None = None, filters: FilterSpec | None = None) -> str | None:
    get_root()
    return filedialog.askopenfilename(title=title, initialdir=initialdir, filetypes=filters or []) or None


def open_multiple(title: str | None = None,
                  initialdir: str | None = None,
                  filters: FilterSpec | None = None) -> List[str]:
    get_root()
    paths = filedialog.askopenfilenames(title=title, initialdir=initialdir, filetypes=filters or [])
    return list(paths) if paths else []


def save_file(title: str | None = None, initialdir: str | None = None) -> str | None:
    get_root()
    return filedialog.asksaveasfilename(title=title, initialdir=initialdir) or None


def open_directory(title: str | None = None, initialdir: str | None = None) -> str | None:
    get_root()
    return filedialog.askdirectory(title=title, initialdir=initialdir) or None
