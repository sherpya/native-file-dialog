# native-file-dialog monorepo

This repository builds and publishes three packages:

- `native-file-dialog` (core pure Python API and fallback logic)
- `native-file-dialog-gtk` (Linux GTK backend extension)
- `native-file-dialog-qt` (Linux Qt backend extension)

Installing `native-file-dialog` on Linux pulls both backend distributions through
platform markers. On macOS and Windows, only core dependencies are installed.

## Runtime behavior

`native_file_dialog` keeps the same backend resolution behavior:

- Linux: try Qt/GTK by desktop preference and fall back to tkinter
- macOS: PyObjC then osascript fallback
- Windows: win32 backend

If a Linux native backend is not installed or fails to import, fallback selection
continues and tkinter remains the final fallback.

## Repository layout

- `packages/core`
- `packages/backend-gtk`
- `packages/backend-qt`
- `docker/gtk.Dockerfile`
- `docker/qt.Dockerfile`
- `.github/workflows/release.yml`
- `VERSION`

## Build backend wheels with Docker (Linux)

GTK:

```bash
docker build -f docker/gtk.Dockerfile -t nfd-gtk .
docker run --rm -v $PWD/packages/backend-gtk:/project nfd-gtk python3 -m build
```

Qt:

```bash
docker build -f docker/qt.Dockerfile -t nfd-qt .
docker run --rm -v $PWD/packages/backend-qt:/project nfd-qt python3 -m build
```

## Core package usage

```python
import native_file_dialog

# Single file selection (returns [path] or None)
paths = native_file_dialog.open_file(title="Choose a file")
if paths:
    print(paths[0])

# Multiple file selection (returns [path1, ...] or None)
paths = native_file_dialog.open_file(title="Choose files", multiple=True)
if paths:
    for p in paths:
        print(p)

# Save file
path = native_file_dialog.save_file(title="Save as")
print(path)

# Directory selection
directory = native_file_dialog.open_directory(title="Select a folder")
print(directory)
```

## Local development

When working on the monorepo locally, `uv`’s resolver cannot see the unpublished
`native-file-dialog` / `native-file-dialog-gtk` / `native-file-dialog-qt`
packages in any index, so you should install them as editables **without**
resolving dependencies from PyPI.

From the repository root, with a virtual environment activated:

```bash
# Core package (pure Python)
uv pip install -e packages/core --no-deps

# Linux backends (build native extensions once)
uv pip install -e packages/backend-gtk --no-deps
uv pip install -e packages/backend-qt --no-deps
```

After this you can import and use the library as usual:

```bash
python -c "import native_file_dialog; print(native_file_dialog.open_file)"
```

## License

MIT. See `LICENSE` for details.
