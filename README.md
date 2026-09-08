# native-file-dialog

[![PyPI](https://img.shields.io/pypi/v/native-file-dialog)](https://pypi.org/project/native-file-dialog/)
[![Python](https://img.shields.io/python/required-version-toml?tomlFilePath=https://raw.githubusercontent.com/sherpya/native-file-dialog/master/packages/core/pyproject.toml)](https://pypi.org/project/native-file-dialog/)
[![License](https://img.shields.io/pypi/l/native-file-dialog)](https://github.com/sherpya/native-file-dialog/blob/master/LICENSE)
[![CI](https://github.com/sherpya/native-file-dialog/actions/workflows/release.yml/badge.svg)](https://github.com/sherpya/native-file-dialog/actions/workflows/release.yml)

This repository builds and publishes four packages:

- `native-file-dialog` (core pure Python API and fallback logic)
- `native-file-dialog-gtk` (Linux GTK4 backend extension, requires GTK 4.10+)
- `native-file-dialog-gtk3` (Linux GTK3 backend extension, requires GTK 3.20+)
- `native-file-dialog-qt` (Linux Qt backend extension)

Installing `native-file-dialog` on Linux pulls all three backend distributions through
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

## Tkinter / CustomTkinter applications

Use the explicit Tk adapter to keep the application's events running while a
Linux GTK/Qt file dialog is open:

```python
import customtkinter as ctk
import native_file_dialog.tkinter as dialogs

root = ctk.CTk()

def choose():
    paths = dialogs.open_file(master=root, filters=[("PDF", "*.pdf")])
    if paths:
        print(paths[0])

ctk.CTkButton(root, text="Open", command=choose).pack()
root.mainloop()
```

`save_file` and `open_directory` accept the same required keyword-only `master`.
Pass the owning `Toplevel` when opening from an existing modal window. The
adapter services Tk timers, redraws and window events in bounded batches;
temporarily shields application input; and releases/restores grabs, focus and
bindings. Destroying the owner cancels the native dialog and returns `None`.
The Tk fallback uses the supplied parent instead of creating another root.
Windows and macOS retain their existing native wait behavior.

`master` associates the request with a Tk interpreter and window lifetime. It
does **not** wrap the Tk window as a GTK/Qt parent or force native placement.
Window-manager/portal placement and focus must still be checked on the target
desktop, particularly the reported tiny, unresponsive chooser on multi-monitor
XFCE. Fixing event starvation is not by itself proof of that issue's cause.

## Integrating another event loop on Linux

The core API also accepts keyword-only `event_pump` for GTK4, GTK3 and Qt:

```python
paths = nfd.open_file(event_pump=process_pending_host_events)
```

The callable runs once before native initialization, then approximately every
20 ms on the calling/main thread while waiting. It must process a bounded batch
of events without blocking or entering another modal wait. Return `None` (or
`True`) to continue, or exactly `False` to cancel. Exceptions, including their
traceback, propagate to the caller after native cleanup. GTK4 cancellation waits
for its asynchronous completion callback before freeing state. The timer and
callback references are removed on completion, cancellation and errors.

Calls remain synchronous with the same return values; omitting `event_pump`
retains the original wait behavior. It is not used by the Tk fallback or on
Windows/macOS. All Linux dialog calls must run on the main thread; concurrent
or nested native dialog requests raise `RuntimeError`. Qt reuses an existing
`QApplication` without owning it, and rejects an incompatible `QCoreApplication`.
Upgrade/rebuild the core and native backend packages together when using the
new callback argument. Application callbacks remain responsible for avoiding
long-running work and nested blocking dialogs.

This integration is cooperative: it cannot interrupt a toolkit's internal
synchronous waits. In particular, an X11 clipboard read by Qt from a Tk owner
in the same process can temporarily suspend the timer and time out. The Tk
adapter does not provide a cross-toolkit clipboard bridge.

## Regression checks

With core/backends installed in the current environment:

```bash
python -m unittest discover -s tests -v
python tests/run_gui_tests.py
python examples/ctk_dialog_probe.py --backend gtk
```

The GUI runner needs CustomTkinter, `Xvfb`, `xauth`, `dbus-daemon` and `xdotool`.
It creates a private display and D-Bus without portal service activation, and
tests each backend in a separate process. Pass `gtk`, `gtk3` or `qt` to restrict
the run. It checks actual native acceptance/cancellation, callback exceptions,
main-thread/reentry guards and Tk/CTk lifecycle and modality.

For the physical XFCE regression, run the probe once per backend and compare
with `--raw`. Test open, multiple selection, save, directory, and a chooser
launched from the existing modal. Check that the chooser fully renders and can
be focused, accepted and cancelled on either monitor; switch focus away and
back, move/resize the windows, and repeat after closing. The heartbeat should
keep advancing with the adapter. Preserve the printed backend/version/session
diagnostics when reporting a failure. The automated suite does not establish
correct placement or portal behavior on a real multi-monitor desktop.

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
