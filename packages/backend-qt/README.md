# native-file-dialog-qt

Linux Qt6 backend for
[native-file-dialog](https://github.com/sherpya/native-file-dialog).
Requires Qt6 Core, Gui and Widgets at runtime. Building from source also requires
a C++ compiler, CMake and Python and Qt6 development headers.

On Debian: `apt install build-essential cmake python3-dev qt6-base-dev`.

The toolkit is an optional system dependency: this wheel does not bundle it
or install it. If it is absent or incompatible, the core skips this backend
and tries its other backends, finally falling back to Tkinter. The manylinux
tag covers the extension runtime baseline, not toolkit availability.

License: MIT. Copyright (c) Gianluigi Tiesi <sherpya@gmail.com>.
