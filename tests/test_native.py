import importlib
import os
import re
import subprocess
from pathlib import Path
import tempfile
import threading
import time
import tkinter as tk
import _tkinter
import unittest

import native_file_dialog as nfd


BACKEND = os.environ.get('NFD_TEST_BACKEND')


@unittest.skipUnless(BACKEND and os.environ.get('DISPLAY'), 'Use run_gui_tests.py')
class NativeTests(unittest.TestCase):
    def test_accept_paths_with_native_widgets(self):
        """Drive real chooser widgets, including the prefilled save name."""
        root = tk.Tk()
        root.withdraw()
        self.addCleanup(root.destroy)
        with tempfile.TemporaryDirectory(prefix='nfd-selection-') as directory:
            base = Path(directory)
            selected = base / 'caffè.pdf'
            selected.touch()
            for operation, extra, expected in [
                ('open_file', {}, [str(selected)]),
                ('open_file', {'multiple': True}, [str(selected)]),
                ('save_file', {'default_name': 'nuovo.pdf'}, str(base / 'nuovo.pdf')),
                ('open_directory', {}, str(base)),
            ]:
                with self.subTest(operation=operation, extra=extra):
                    title = f'NFD acceptance {operation}'
                    root.clipboard_clear()
                    root.clipboard_append(str(selected))
                    root.update()
                    finished = threading.Event()
                    errors = []
                    def xdo(*args):
                        return subprocess.run(['xdotool', *args], capture_output=True, text=True, timeout=2)
                    def accept():
                        try:
                            deadline = time.monotonic() + 10
                            window = None
                            while not finished.wait(.1) and time.monotonic() < deadline:
                                windows = xdo('search', '--onlyvisible', '--name', re.escape(title)).stdout.split()
                                if windows:
                                    window = windows[-1]
                                    break
                            if window is None:
                                raise AssertionError('Native chooser did not become visible')
                            xdo('windowmove', window, '300', '100')
                            xdo('windowfocus', window)
                            finished.wait(.3)
                            if operation == 'open_file':
                                if BACKEND == 'qt':
                                    # The runner uses Qt's plain QFileDialog at 96 DPI.
                                    # Select its sole file in the first row. Avoid an
                                    # X11 clipboard transfer between Tk and Qt: Qt's
                                    # synchronous clipboard read does not service timers.
                                    xdo('mousemove', '--window', window, '190', '70')
                                    xdo('click', '1')
                                else:
                                    xdo('key', '--window', window, 'ctrl+l')
                                    finished.wait(.2)
                                    xdo('key', '--window', window, 'ctrl+a')
                                    finished.wait(.1)
                                    xdo('key', '--window', window, 'ctrl+v')
                                    finished.wait(.3)
                            # Open accepts the typed path; directory/save accept their
                            # initial directory/default name, without typing replacements.
                            for _ in range(4):
                                if finished.is_set():
                                    return
                                if window not in xdo('search', '--onlyvisible', '--name', re.escape(title)).stdout.split():
                                    return
                                xdo('key', '--window', window, 'Return')
                                if finished.wait(1):
                                    return
                        except Exception as error:
                            errors.append(error)
                    worker = threading.Thread(target=accept, daemon=True)
                    worker.start()
                    start = time.monotonic()
                    calls = []
                    def pump():
                        for _ in range(32):
                            if not root.tk.dooneevent(_tkinter.ALL_EVENTS | _tkinter.DONT_WAIT):
                                break
                        calls.append(1)
                        if errors:
                            raise errors[0]
                        if time.monotonic() - start > 15:
                            if artifact_dir := os.environ.get('NFD_TEST_ARTIFACTS'):
                                from PIL import ImageGrab
                                Path(artifact_dir).mkdir(parents=True, exist_ok=True)
                                ImageGrab.grab().save(Path(artifact_dir) / f'{BACKEND}-{operation}.png')
                            raise AssertionError('Native chooser did not accept the selection')
                    try:
                        result = getattr(nfd, operation)(title=title, initialdir=base,
                                                          backend=BACKEND, event_pump=pump, **extra)
                    finally:
                        finished.set()
                        worker.join(3)
                    if operation == 'open_directory':
                        self.assertEqual(Path(result), Path(expected))
                    else:
                        self.assertEqual(result, expected)
                    self.assertGreater(len(calls), 1)
                    self.assertFalse(errors)

    def test_all_operations_cancel_from_timer_and_reopen(self):
        for operation, extra in [('open_file', {}), ('open_file', {'multiple': True}),
                                 ('save_file', {'default_name': 'caffè.pdf'}), ('open_directory', {})]:
            with self.subTest(operation=operation, extra=extra):
                calls = []
                def pump():
                    calls.append(threading.current_thread())
                    return False if len(calls) >= 5 else None
                result = getattr(nfd, operation)(backend=BACKEND, initialdir=Path(tempfile.gettempdir()),
                                                  event_pump=pump, **extra)
                self.assertIsNone(result)
                self.assertEqual(len(calls), 5)
                self.assertTrue(all(thread is threading.main_thread() for thread in calls))

    def test_callback_exception_preserves_identity_and_stops_timer(self):
        sentinel = ValueError('callback failure')
        calls = []
        def pump():
            calls.append(1)
            if len(calls) == 5:
                raise sentinel
        with self.assertRaises(ValueError) as caught:
            nfd.open_file(backend=BACKEND, event_pump=pump)
        self.assertIs(caught.exception, sentinel)
        self.assertIsNone(nfd.open_file(backend=BACKEND, event_pump=lambda: False))
        # A second running native loop would dispatch a leaked timer from the first.
        second = []
        def next_pump():
            second.append(1)
            return False if len(second) == 5 else None
        nfd.open_directory(backend=BACKEND, event_pump=next_pump)
        self.assertEqual(len(calls), 5)

    def test_native_reentry_cannot_overwrite_active_state(self):
        extension = importlib.import_module(f'native_file_dialog_{BACKEND}')
        calls = []
        def pump():
            calls.append(1)
            with self.assertRaisesRegex(RuntimeError, 'already active'):
                extension.open_directory('', '/tmp')
            return False if len(calls) == 4 else None
        nfd.open_file(backend=BACKEND, event_pump=pump)
        self.assertEqual(len(calls), 4)

    def test_direct_native_worker_thread_rejected(self):
        extension = importlib.import_module(f'native_file_dialog_{BACKEND}')
        errors = []
        def worker():
            try:
                extension.open_directory('', '/tmp')
            except RuntimeError as error:
                errors.append(str(error))
        thread = threading.Thread(target=worker)
        thread.start()
        thread.join(2)
        self.assertFalse(thread.is_alive())
        self.assertEqual(len(errors), 1)
        self.assertIn('main thread', errors[0])

    def test_ctk_timers_continue_and_destroying_owner_cancels(self):
        import customtkinter as ctk
        import native_file_dialog.tkinter as dialogs
        root = ctk.CTk()
        root.geometry('400x200')
        root.update()
        top = ctk.CTkToplevel(root)
        top.update()
        top.grab_set()
        ticks = []
        errors = []
        root.report_callback_exception = lambda *args: errors.append(args)
        result = []
        def tick():
            ticks.append(time.monotonic())
            root.after(30, tick)
        def open_dialog():
            start = len(ticks)
            root.after(500, top.destroy)
            result.append(dialogs.open_file(master=top, backend=BACKEND))
            self.assertGreater(len(ticks)-start, 2)
            self.assertIsNone(root.grab_current())
            root.after(100, root.quit)
        try:
            tick()
            root.after(50, open_dialog)
            root.mainloop()
            self.assertEqual(result, [None])
            self.assertFalse(errors)
            self.assertFalse(root.tk.call('tk', 'busy', 'status', '.'))
        finally:
            for job in root.tk.call('after', 'info'):
                root.after_cancel(job)
            root.destroy()


if __name__ == '__main__':
    unittest.main()
