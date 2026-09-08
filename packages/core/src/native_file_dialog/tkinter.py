"""Synchronous native dialogs integrated with a Tk/CustomTkinter application.

Pass an explicit ``master`` owned by the main thread. On Linux, native GTK/Qt
dialogs service Tk events while temporarily shielding the application's input.
``master`` identifies the Tk interpreter and lifetime; it is not a foreign GTK
or Qt window handle and does not force native window placement.
"""
from __future__ import annotations

import _tkinter
import os
import sys
import threading
import time
import tkinter as tk

from . import Backend, FilterSpec, PathLike, _call_backend, resolve_backend

__all__ = ['open_file', 'save_file', 'open_directory']

_active_interpreters: set[int] = set()


class _TkModal:
    """Own only the temporary grabs, busy windows and bindtags we install."""

    def __init__(self, master: tk.Misc):
        self.master = master
        self.tk = master.tk
        self.tag = f'nfd_modal_{id(self)}'
        self.tagged: set[str] = set()
        self.busy: set[str] = set()
        self.focus = ''
        self.grab: tuple[str, str] | None = None

    def _exists(self, window: str) -> bool:
        try:
            return bool(self.tk.getboolean(self.tk.call('winfo', 'exists', window)))
        except tk.TclError:
            return False

    @property
    def alive(self) -> bool:
        return self._exists(str(self.master))

    def _release_grab(self) -> None:
        current = str(self.tk.call('grab', 'current', str(self.master)))
        if current:
            self.grab = current, str(self.tk.call('grab', 'status', current))
            self.tk.call('grab', 'release', current)

    def _protect_windows(self) -> None:
        # Include new windows created by timer/background-result callbacks.
        pending = ['.']
        while pending:
            window = pending.pop()
            if not self._exists(window):
                continue
            tags = self.tk.splitlist(self.tk.call('bindtags', window))
            if self.tag not in tags:
                self.tk.call('bindtags', window, (self.tag, *tags))
                self.tagged.add(window)
            if str(self.tk.call('winfo', 'toplevel', window)) == window:
                if not self.tk.getboolean(self.tk.call('tk', 'busy', 'status', window)):
                    self.tk.call('tk', 'busy', 'hold', window)
                    self.busy.add(window)
            pending.extend(self.tk.splitlist(self.tk.call('winfo', 'children', window)))
        self._release_grab()

    def __enter__(self):
        if threading.current_thread() is not threading.main_thread():
            raise RuntimeError('Tk file dialogs must run on the main thread')
        key = id(self.tk)
        if key in _active_interpreters:
            raise RuntimeError('A native file dialog is already active for this Tk application')
        _active_interpreters.add(key)
        try:
            if self.alive:
                self.focus = str(self.tk.call('focus'))
                # Prepend the tag so widget, class and bind_all shortcuts cannot run.
                for sequence in ('<KeyPress>', '<KeyRelease>', '<ButtonPress>',
                                 '<ButtonRelease>', '<MouseWheel>', '<<Drop>>', '<<Drop:DND_Files>>'):
                    self.tk.call('bind', self.tag, sequence, 'break')
                self._protect_windows()
                self.master.update_idletasks()
            return self
        except BaseException:
            self.__exit__(*sys.exc_info())
            raise

    def pump(self) -> bool | None:
        if not self.alive:
            return False
        try:
            self._protect_windows()
            deadline = time.monotonic() + .005
            for _ in range(64):
                if not self.tk.dooneevent(_tkinter.ALL_EVENTS | _tkinter.DONT_WAIT):
                    break
                if not self.alive:
                    return False
                if time.monotonic() >= deadline:
                    break
            self._protect_windows()
        except tk.TclError:
            if not self.alive:
                return False
            raise
        return None

    def __exit__(self, *_):
        try:
            for window in self.busy:
                if self._exists(window) and self.tk.getboolean(self.tk.call('tk', 'busy', 'status', window)):
                    self.tk.call('tk', 'busy', 'forget', window)
            for window in self.tagged:
                if self._exists(window):
                    tags = self.tk.splitlist(self.tk.call('bindtags', window))
                    self.tk.call('bindtags', window, tuple(tag for tag in tags if tag != self.tag))
            # The interpreter survives destruction of its root, but Tk commands may not.
            for sequence in self.tk.splitlist(self.tk.call('bind', self.tag)):
                self.tk.call('bind', self.tag, sequence, '')
            if self.grab and self._exists(self.grab[0]):
                if not self.tk.call('grab', 'current', self.grab[0]):
                    args = ('-global', self.grab[0]) if self.grab[1] == 'global' else (self.grab[0],)
                    self.tk.call('grab', 'set', *args)
            if self.focus and self._exists(self.focus):
                self.tk.call('focus', '-force', self.focus)
        except tk.TclError:
            if self._exists('.'):
                raise
        finally:
            _active_interpreters.discard(id(self.tk))


def _dialog(operation: str, master: tk.Misc, backend: Backend | None, **kwargs):
    module = resolve_backend(backend)
    kwargs['title'] = kwargs.get('title') or ''
    kwargs['initialdir'] = os.fspath(kwargs['initialdir']) if kwargs.get('initialdir') else '.'
    if module.__name__.rsplit('.', 1)[-1] == 'tk':
        return _call_backend(module, operation, parent=master, **kwargs)
    if sys.platform != 'linux':
        return _call_backend(module, operation, **kwargs)
    with _TkModal(master) as modal:
        if not modal.alive:
            return None
        result = _call_backend(module, operation, event_pump=modal.pump, **kwargs)
        return result if modal.alive else None


def open_file(title: str | None = None, initialdir: PathLike | None = None,
              filters: FilterSpec | None = None, multiple: bool = False,
              backend: Backend | None = None, *, master: tk.Misc) -> list[str] | None:
    return _dialog('open_file', master, backend, title=title, initialdir=initialdir,
                   filters=filters, multiple=multiple)


def save_file(title: str | None = None, initialdir: PathLike | None = None,
              filters: FilterSpec | None = None, default_name: str | None = None,
              backend: Backend | None = None, *, master: tk.Misc) -> str | None:
    return _dialog('save_file', master, backend, title=title, initialdir=initialdir,
                   filters=filters, default_name=default_name)


def open_directory(title: str | None = None, initialdir: PathLike | None = None,
                   backend: Backend | None = None, *, master: tk.Misc) -> str | None:
    return _dialog('open_directory', master, backend, title=title, initialdir=initialdir)
