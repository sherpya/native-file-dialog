# native-file-dialog

Synchronous open, save and directory dialogs for Python 3.11+, with native
Windows, macOS and Linux backends and a Tkinter fallback. Includes a Tkinter /
CustomTkinter adapter that keeps the Tk event loop responsive on Linux.

```python
from native_file_dialog import tkinter as dialogs

paths = dialogs.open_file(master=root, filters=[("PDF files", "*.pdf")])
```

Pass an existing Tk window as `root`. On Linux, the core depends on the GTK4,
GTK3 and Qt backend packages; each is used only when its corresponding system toolkit can be loaded.
The backend wheels do not install or bundle GTK/Qt. Missing toolkits are skipped,
with Tkinter as the final fallback.

[Documentation and source](https://github.com/sherpya/native-file-dialog)

License: MIT. Copyright (c) Gianluigi Tiesi <sherpya@gmail.com>.
