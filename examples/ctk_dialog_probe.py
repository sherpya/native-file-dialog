"""Interactive Linux regression probe. Run each GTK major in a fresh process."""
import argparse
import importlib.metadata
import os
import platform
import sys
import time
import traceback

import customtkinter as ctk
import native_file_dialog as native
import native_file_dialog.tkinter as dialogs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backend', choices=['gtk', 'gtk3', 'qt', 'tk'])
    parser.add_argument('--raw', action='store_true', help='Use the original blocking API for comparison')
    args = parser.parse_args()
    backend = native.resolve_backend(args.backend)
    print('Python:', sys.version, '\nSystem:', platform.platform(), flush=True)
    print('Backend:', backend.__name__, '\nCore:', native.__file__, flush=True)
    for name in ('customtkinter', 'native-file-dialog', 'native-file-dialog-gtk',
                 'native-file-dialog-gtk3', 'native-file-dialog-qt'):
        try:
            print(f'{name}: {importlib.metadata.version(name)}', flush=True)
        except importlib.metadata.PackageNotFoundError:
            pass
    for name in ('XDG_CURRENT_DESKTOP', 'XDG_SESSION_TYPE', 'DISPLAY', 'WAYLAND_DISPLAY',
                 'GDK_SCALE', 'QT_SCALE_FACTOR'):
        print(f'{name}: {os.environ.get(name, "")}', flush=True)

    root = ctk.CTk()
    root.title('Native file dialog / CTk probe')
    root.geometry('640x440')
    ctk.CTkLabel(root, text=f'{backend.__name__.rsplit(".", 1)[-1]} — {"raw" if args.raw else "Tk integration"}').pack(pady=10)
    heartbeat = ctk.CTkLabel(root, text='')
    heartbeat.pack()
    ctk.CTkLabel(root, text='Move and resize the windows, switch monitors and focus.\n'
                          'The counter should keep advancing while the file dialog is open.').pack(pady=10)
    result_label = ctk.CTkLabel(root, text='No result yet', wraplength=580)
    result_label.pack(pady=10)
    last = time.monotonic()
    ticks = 0

    def tick():
        nonlocal ticks, last
        now = time.monotonic()
        ticks += 1
        heartbeat.configure(text=f'Tk heartbeat: {ticks}   interval: {now-last:.3f}s')
        if now-last > .5:
            print(f'Tk heartbeat gap: {now-last:.3f}s', flush=True)
        last = now
        root.after(100, tick)

    def choose(operation, owner=root, multiple=False):
        options = dict(backend=args.backend, initialdir=os.path.expanduser('~'))
        if operation != 'open_directory':
            options['filters'] = [('PDF and text', '*.pdf;*.txt'), ('All files', '*')]
        if operation == 'open_file':
            options['multiple'] = multiple
        elif operation == 'save_file':
            options['default_name'] = 'caffè.pdf'
        if not args.raw:
            options['master'] = owner
        print(f'Opening {operation}; multiple={multiple}; owner={owner}', flush=True)
        try:
            result = getattr(native if args.raw else dialogs, operation)(**options)
            print('Result:', repr(result), flush=True)
            if root.winfo_exists():
                result_label.configure(text=repr(result))
        except Exception:
            traceback.print_exc()

    for label, operation, multi in [('Open', 'open_file', False), ('Open multiple', 'open_file', True),
                                     ('Save', 'save_file', False), ('Directory', 'open_directory', False)]:
        ctk.CTkButton(root, text=label, command=lambda op=operation, m=multi: choose(op, multiple=m)).pack(pady=3)

    def nested():
        top = ctk.CTkToplevel(root)
        top.title('Existing modal / grab restoration')
        top.geometry('420x180')
        top.transient(root)
        ctk.CTkButton(top, text='Open from this modal', command=lambda: choose('open_file', top)).pack(pady=25)
        ctk.CTkButton(top, text='Close', command=top.destroy).pack()
        top.wait_visibility()
        top.grab_set()

    ctk.CTkButton(root, text='Existing modal window', command=nested).pack(pady=3)
    tick()
    root.mainloop()


if __name__ == '__main__':
    main()
