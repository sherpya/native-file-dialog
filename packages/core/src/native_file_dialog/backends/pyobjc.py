"""
    macOS native file dialog backend via PyObjC (NSOpenPanel / NSSavePanel).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .. import FilterSpec
    from typing import List

from AppKit import NSOpenPanel, NSSavePanel  # type: ignore
from Foundation import NSURL  # type: ignore
from UniformTypeIdentifiers import UTType  # type: ignore[import-untyped]


def filter_to_ut_types(filter_spec: FilterSpec) -> List[UTType]:
    """Extract UTTypes from glob patterns like '*.py', '*.md'"""
    ut_types = []
    for _, pattern in filter_spec:
        if pattern.startswith('*.'):
            ext = pattern[2:]  # 'py', 'md'
            if ut_type := UTType.typeWithFilenameExtension_(ext):
                ut_types.append(ut_type)
    return ut_types


def open_file(title: str | None = None, initialdir: str | None = None, filters: FilterSpec | None = None) -> str | None:
    panel = NSOpenPanel.openPanel()
    panel.setCanChooseFiles_(True)
    panel.setCanChooseDirectories_(False)
    panel.setAllowsMultipleSelection_(False)

    if title:
        panel.setTitle_(title)

    if initialdir:
        panel.setDirectoryURL_(NSURL.fileURLWithPath_(initialdir))

    if filters:
        types = filter_to_ut_types(filters)
        print(types)
        panel.setAllowedContentTypes_(types)

    if panel.runModal() != 1:
        return None

    urls = panel.URLs()
    if not urls or urls.count() == 0:
        return None
    return urls[0].path()


def open_multiple(title: str | None = None,
                  initialdir: str | None = None,
                  filters: FilterSpec | None = None) -> List[str]:
    panel = NSOpenPanel.openPanel()
    panel.setCanChooseFiles_(True)
    panel.setCanChooseDirectories_(False)
    panel.setAllowsMultipleSelection_(True)

    if title:
        panel.setTitle_(title)

    if initialdir:
        panel.setDirectoryURL_(NSURL.fileURLWithPath_(initialdir))

    if filters:
        types = filter_to_ut_types(filters)
        panel.setAllowedContentTypes_(types)

    if panel.runModal() != 1:
        return []

    urls = panel.URLs()
    if not urls:
        return []

    return [url.path() for url in urls]


def save_file(title: str | None = None, initialdir: str | None = None) -> str | None:
    panel = NSSavePanel.savePanel()

    if title:
        panel.setTitle_(title)

    if initialdir:
        panel.setDirectoryURL_(NSURL.fileURLWithPath_(initialdir))

    if panel.runModal() != 1:
        return None

    url = panel.URL()
    return url.path() if url else None


def open_directory(title: str | None = None, initialdir: str | None = None) -> str | None:
    panel = NSOpenPanel.openPanel()
    panel.setCanChooseFiles_(False)
    panel.setCanChooseDirectories_(True)
    panel.setAllowsMultipleSelection_(False)

    if title:
        panel.setTitle_(title)

    if initialdir:
        panel.setDirectoryURL_(NSURL.fileURLWithPath_(initialdir))

    if panel.runModal() != 1:
        return None

    urls = panel.URLs()
    if not urls or urls.count() == 0:
        return None
    return urls[0].path()
