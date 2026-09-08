# native-file-dialog-gtk3

Linux GTK3 backend for
[native-file-dialog](https://github.com/sherpya/native-file-dialog).
Requires GTK 3.20+ at runtime. Building from source also requires a C compiler,
CMake, pkg-config and Python and GTK3 development headers.

On Debian: `apt install build-essential cmake pkg-config python3-dev libgtk-3-dev`.

GTK3 and GTK4 backends must run in separate processes.

The toolkit is an optional system dependency: this wheel does not bundle it
or install it. If it is absent or incompatible, the core skips this backend
and tries its other backends, finally falling back to Tkinter. The manylinux
tag covers the extension runtime baseline, not toolkit availability.

License: MIT. Copyright (c) Gianluigi Tiesi <sherpya@gmail.com>.
