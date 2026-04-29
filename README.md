# native-file-dialog

![Python 3.11+](https://img.shields.io/badge/python-3.11%20|%203.12%20|%203.13%20|%203.14-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)
![Platform: Linux | macOS | Windows](https://img.shields.io/badge/platform-Linux%20|%20macOS%20|%20Windows-lightgrey)

This repository builds and publishes four packages:

- `native-file-dialog` (core pure Python API and fallback logic)
- `native-file-dialog-gtk` (Linux GTK4 backend extension, requires GTK 4.10+)
- `native-file-dialog-gtk3` (Linux GTK3 backend extension, requires GTK 3.20+)
- `native-file-dialog-qt` (Linux Qt backend extension)

Installing `native-file-dialog` on Linux pulls both backend distributions through
platform markers. On macOS and Windows, only core dependencies are installed.

## Runtime behavior

`native_file_dialog` keeps the same backend resolution behavior:

- Linux: try Qt/GTK by desktop preference and fall back to tkinter
- macOS: PyObjC with tkinter fallback
- Windows: win32 backend

If a Linux native backend is not installed or fails to import, fallback selection
continues and tkinter remains the final fallback.

GTK3 and GTK4 cannot be mixed in the same Python process. Once one GTK backend
has been imported, later attempts to use the other GTK major version fail with a
clear `RuntimeError`; use one GTK backend consistently or run the other in a
subprocess.

## Repository layout

- `packages/core`
- `packages/backend-gtk` (GTK4 backend, shared C source)
- `packages/backend-gtk3` (GTK3 backend, references shared C source)
- `packages/backend-qt`
- `docker/gtk.Dockerfile` (trixie, GTK4)
- `docker/gtk3.Dockerfile` (bookworm, GTK3)
- `docker/qt.Dockerfile`
- `.github/workflows/release.yml`
- `VERSION`

## Build backend wheels with Docker (Linux)

GTK4 (Debian trixie):

```bash
docker build -f docker/gtk.Dockerfile -t nfd-gtk .
docker run --rm -v $PWD/packages:/packages nfd-gtk python3 -m build
```

GTK3 (Debian bookworm):

```bash
docker build -f docker/gtk3.Dockerfile -t nfd-gtk3 .
docker run --rm -v $PWD/packages:/packages nfd-gtk3 python3 -m build
```

Qt:

```bash
docker build -f docker/qt.Dockerfile -t nfd-qt .
docker run --rm -v $PWD/packages/backend-qt:/project nfd-qt python3 -m build
```

## Usage

```python
import native_file_dialog as nfd

# Single file selection (returns [path] or None)
paths = nfd.open_file(title="Choose a file")
if paths:
    print(paths[0])

# Multiple file selection (returns [path1, ...] or None)
paths = nfd.open_file(title="Choose files", multiple=True)
if paths:
    for p in paths:
        print(p)

# File selection with filters
paths = nfd.open_file(title="Open PDF", filters=[("PDF files", "*.pdf")])

# Save file
path = nfd.save_file(title="Save as")
print(path)

# Save file with filters
path = nfd.save_file(title="Export PDF", filters=[("PDF files", "*.pdf")])
print(path)

# Directory selection
directory = nfd.open_directory(title="Select a folder")
print(directory)

# Force a specific backend ('gtk', 'gtk3', 'qt', 'tk', 'pyobjc')
paths = nfd.open_file(title="Pick", backend="gtk")
```

## macOS PyObjC backend

The `pyobjc` backend uses native Cocoa dialogs (`NSOpenPanel` / `NSSavePanel`).
Install the required frameworks:

```bash
pip install pyobjc-framework-Cocoa pyobjc-framework-UniformTypeIdentifiers
```

- `pyobjc-framework-Cocoa` provides `AppKit` and `Foundation` (open/save/directory dialogs)
- `pyobjc-framework-UniformTypeIdentifiers` provides `UTType` (filter support in save dialogs)

If neither package is installed, the backend falls back to tkinter.

## Local development

When working on the monorepo locally, `uv`’s resolver cannot see the unpublished
`native-file-dialog` / `native-file-dialog-gtk` / `native-file-dialog-gtk3` /
`native-file-dialog-qt` packages in any index, so you should install them as
editables **without** resolving dependencies from PyPI.

From the repository root, with a virtual environment activated:

```bash
# Core package (pure Python)
uv pip install -e packages/core --no-deps

# Linux backends (build native extensions once)
uv pip install -e packages/backend-gtk --no-deps
uv pip install -e packages/backend-gtk3 --no-deps
uv pip install -e packages/backend-qt --no-deps
```

After this you can import and use the library as usual:

```python
import native_file_dialog as nfd
print(nfd.open_file)
```

## License

MIT. See `LICENSE` for details.
