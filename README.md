# native-file-dialog

A Python library for native file dialogs (open, save, multiple selection, directory picker),
with a single API across platforms.

## Features

- **Linux**: Qt6 or GTK4/libadwaita native extensions (chosen via `XDG_CURRENT_DESKTOP`), with tkinter fallback
- **Windows**: ctypes (`GetOpenFileNameW` / `GetSaveFileNameW` / `SHBrowseForFolderW`) — no external dependencies
- **macOS**: osascript (AppleScript) or optional PyObjC

## Installation

```bash
pip install native-file-dialog
```

Optional platform-specific dependencies:

- **macOS** (more native): `pip install pyobjc-framework-Cocoa pyobjc-framework-uniformtypeidentifiers`

On **Linux**, the Qt and GTK extensions are built only when compiling from source on Linux. Build dependencies (e.g. Debian/Ubuntu):

```bash
# Qt6 extension
sudo apt install qt6-base-dev

# GTK4 extension
sudo apt install libgtk-4-dev libadwaita-1-dev

# Build (e.g. with uv)
uv pip install -e .
```

## Usage

```python
import native_file_dialog

# Single file
path = native_file_dialog.open_file(
    title='Choose a file',
    initialdir='/home/user',
    filters=[('Python Files', '*.py'), ('Markdown Files', '*.md')],
)
if path:
    print(path)

# Multiple files
paths = native_file_dialog.open_multiple(
    title='Choose files',
    filters=[('Python Files', '*.py'), ('All', '*')],
)
print(paths)

# Save file
path = native_file_dialog.save_file(title='Save as', initialdir='/home/user')
if path:
    print(path)

# Choose directory
directory = native_file_dialog.open_directory(
    title='Select a folder',
    initialdir='/home/user',
)
if directory:
    print(directory)
```

### Filter format

`filters` is a list of `(description, pattern)` tuples:

```python
filters=[
    ('Python files', '*.py'),
    ('Markdown files', '*.md'),
    ('All files', '*'),
]
```

## Forcing a backend

You can skip autodetect and force a backend with the optional `backend` parameter:

```python
# Force GTK (Linux)
path = native_file_dialog.open_file(backend='gtk')

# Force Qt/KDE (Linux)
path = native_file_dialog.open_file(backend='qt')

# Force tkinter (any platform)
path = native_file_dialog.open_file(backend='tk')
```

Valid values: `'gtk'`, `'qt'` (Linux only), `'pyobc'`, `'osascript'` (macOS only), `'tk'` (any platform).

## Linux backend selection (autodetect)

On Linux, when `backend` is not set, the backend is chosen from `XDG_CURRENT_DESKTOP`:

- **KDE**: try Qt extension first, then GTK, then tkinter
- **GNOME** (and similar): try GTK first, then Qt, then tkinter
- **Other**: try Qt first, then GTK, then tkinter

If an extension fails to load (e.g. missing libraries), the next backend is tried;
tkinter is always used as fallback.

## License

MIT. See [LICENSE](LICENSE) for details.
