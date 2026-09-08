# native-file-dialog-gtk

Linux GTK4/libadwaita backend for
[native-file-dialog](https://github.com/sherpya/native-file-dialog).
Requires GTK 4.10+ and libadwaita at runtime. Building from source also requires
a C compiler, CMake, pkg-config and Python, GTK4 and libadwaita development headers.

On Debian trixie: `apt install build-essential cmake pkg-config python3-dev libgtk-4-dev libadwaita-1-dev`.

The toolkit is an optional system dependency: this wheel does not bundle it
or install it. If it is absent or incompatible, the core skips this backend
and tries its other backends, finally falling back to Tkinter. The manylinux
tag covers the extension runtime baseline, not toolkit availability.

License: MIT. Copyright (c) Gianluigi Tiesi <sherpya@gmail.com>.
