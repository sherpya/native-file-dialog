"""
    Windows file dialog backend using ctypes (no external dependencies).
"""

from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import os
from ctypes import (
    POINTER, Structure, byref, c_void_p, c_wchar_p, create_unicode_buffer, sizeof,
)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import List
    from .. import FilterSpec

# comdlg32: GetOpenFileNameW / GetSaveFileNameW

OFN_EXPLORER = 0x00080000
OFN_PATHMUSTEXIST = 0x00001000
OFN_FILEMUSTEXIST = 0x00002000
OFN_ALLOWMULTISELECT = 0x00000200
OFN_OVERWRITEPROMPT = 0x00000002
OFN_NOCHANGEDIR = 0x00000008

MAX_PATH_BUF = 32768


class OPENFILENAMEW(Structure):
    _fields_ = [
        ('lStructSize', wt.DWORD),
        ('hwndOwner', wt.HWND),
        ('hInstance', wt.HINSTANCE),
        ('lpstrFilter', c_wchar_p),
        ('lpstrCustomFilter', c_wchar_p),
        ('nMaxCustFilter', wt.DWORD),
        ('nFilterIndex', wt.DWORD),
        ('lpstrFile', ctypes.POINTER(wt.WCHAR)),
        ('nMaxFile', wt.DWORD),
        ('lpstrFileTitle', c_wchar_p),
        ('nMaxFileTitle', wt.DWORD),
        ('lpstrInitialDir', c_wchar_p),
        ('lpstrTitle', c_wchar_p),
        ('Flags', wt.DWORD),
        ('nFileOffset', wt.WORD),
        ('nFileExtension', wt.WORD),
        ('lpstrDefExt', c_wchar_p),
        ('lCustData', c_void_p),
        ('lpfnHook', c_void_p),
        ('lpTemplateName', c_wchar_p),
        ('pvReserved', c_void_p),
        ('dwReserved', wt.DWORD),
        ('FlagsEx', wt.DWORD),
    ]


_comdlg32 = ctypes.windll.comdlg32
_comdlg32.GetOpenFileNameW.argtypes = [POINTER(OPENFILENAMEW)]
_comdlg32.GetOpenFileNameW.restype = wt.BOOL
_comdlg32.GetSaveFileNameW.argtypes = [POINTER(OPENFILENAMEW)]
_comdlg32.GetSaveFileNameW.restype = wt.BOOL

# shell32: SHBrowseForFolderW / SHGetPathFromIDListW

BIF_RETURNONLYFSDIRS = 0x00000001
BIF_NEWDIALOGSTYLE = 0x00000040
BIF_EDITBOX = 0x00000010

BFFCALLBACK = ctypes.WINFUNCTYPE(ctypes.c_int, wt.HWND, ctypes.c_uint, c_void_p, c_void_p)
BFFM_INITIALIZED = 1
BFFM_SETSELECTION = 0x0467  # WM_USER + 103, Unicode variant


class BROWSEINFOW(Structure):
    _fields_ = [
        ('hwndOwner', wt.HWND),
        ('pidlRoot', c_void_p),
        ('pszDisplayName', ctypes.POINTER(wt.WCHAR)),
        ('lpszTitle', c_wchar_p),
        ('ulFlags', ctypes.c_uint),
        ('lpfn', BFFCALLBACK),
        ('lParam', c_void_p),
        ('iImage', ctypes.c_int),
    ]


_shell32 = ctypes.windll.shell32
_shell32.SHBrowseForFolderW.argtypes = [POINTER(BROWSEINFOW)]
_shell32.SHBrowseForFolderW.restype = c_void_p
_shell32.SHGetPathFromIDListW.argtypes = [c_void_p, ctypes.POINTER(wt.WCHAR)]
_shell32.SHGetPathFromIDListW.restype = wt.BOOL

_ole32 = ctypes.windll.ole32
_ole32.CoTaskMemFree.argtypes = [c_void_p]
_ole32.CoTaskMemFree.restype = None


def _filter_string(filters: FilterSpec | None) -> str:
    """Build Win32 filter string: 'Desc\\0pattern\\0Desc2\\0pattern2\\0\\0'."""
    if not filters:
        return 'All files\x00*.*\x00\x00'
    parts = []
    for desc, pattern in filters:
        parts.append(desc)
        parts.append(pattern)
    return '\x00'.join(parts) + '\x00\x00'


def _resolve_dir(initialdir: str | None) -> str:
    d = os.path.abspath(initialdir or '.')
    return d if os.path.isdir(d) else (os.path.expanduser('~') or '.')


def _make_ofn(title: str | None, initialdir: str | None, filters: FilterSpec | None,
              file_buf: ctypes.Array, flags: int) -> OPENFILENAMEW:
    ofn = OPENFILENAMEW()
    ofn.lStructSize = sizeof(OPENFILENAMEW)
    ofn.lpstrFilter = _filter_string(filters)
    ofn.nFilterIndex = 1
    ofn.lpstrFile = ctypes.cast(file_buf, POINTER(wt.WCHAR))
    ofn.nMaxFile = MAX_PATH_BUF
    ofn.lpstrInitialDir = _resolve_dir(initialdir)
    ofn.lpstrTitle = title or None
    ofn.Flags = flags
    return ofn


def open_file(title: str | None = None, initialdir: str | None = None,
              filters: FilterSpec | None = None, multiple: bool = False) -> List[str] | None:
    buf = create_unicode_buffer(MAX_PATH_BUF)
    flags = OFN_EXPLORER | OFN_PATHMUSTEXIST | OFN_FILEMUSTEXIST | OFN_NOCHANGEDIR
    if multiple:
        flags |= OFN_ALLOWMULTISELECT
    default_title = 'Choose one or more files' if multiple else 'Choose a file'
    ofn = _make_ofn(title or default_title, initialdir, filters, buf, flags)

    if not _comdlg32.GetOpenFileNameW(byref(ofn)):
        return None

    if multiple:
        raw = ctypes.wstring_at(buf, MAX_PATH_BUF)
        parts = [p for p in raw.split('\x00') if p]
        if not parts:
            return None
        if len(parts) == 1:
            return [parts[0]]
        directory = parts[0]
        return [os.path.join(directory, f) for f in parts[1:]]

    return [buf.value] if buf.value else None


def save_file(title: str | None = None, initialdir: str | None = None) -> str | None:
    buf = create_unicode_buffer(MAX_PATH_BUF)
    ofn = _make_ofn(title or 'Save file', initialdir, None, buf,
                    OFN_EXPLORER | OFN_PATHMUSTEXIST | OFN_OVERWRITEPROMPT | OFN_NOCHANGEDIR)
    if not _comdlg32.GetSaveFileNameW(byref(ofn)):
        return None
    return buf.value or None


def open_directory(title: str | None = None, initialdir: str | None = None) -> str | None:
    resolved_dir = _resolve_dir(initialdir)

    @BFFCALLBACK
    def _browse_callback(hwnd, msg, _lp, _data):
        if msg == BFFM_INITIALIZED:
            ctypes.windll.user32.SendMessageW(hwnd, BFFM_SETSELECTION, 1, c_wchar_p(resolved_dir))
        return 0

    display_buf = create_unicode_buffer(MAX_PATH_BUF)
    bi = BROWSEINFOW()
    bi.pszDisplayName = ctypes.cast(display_buf, POINTER(wt.WCHAR))
    bi.lpszTitle = title or 'Select Folder'
    bi.ulFlags = BIF_RETURNONLYFSDIRS | BIF_NEWDIALOGSTYLE | BIF_EDITBOX
    bi.lpfn = _browse_callback

    if not (pidl := _shell32.SHBrowseForFolderW(byref(bi))):
        return None

    path_buf = create_unicode_buffer(MAX_PATH_BUF)
    ok = _shell32.SHGetPathFromIDListW(pidl, ctypes.cast(path_buf, POINTER(wt.WCHAR)))
    _ole32.CoTaskMemFree(pidl)

    if not ok:
        return None

    return path_buf.value or None
