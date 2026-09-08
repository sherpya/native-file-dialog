import os
import time
import tkinter as tk
import types
import unittest
from unittest.mock import Mock, patch

import native_file_dialog.tkinter as dialogs
from native_file_dialog.backends import tk as fallback


@unittest.skipUnless(os.environ.get('DISPLAY'), 'Needs an X display')
class TkTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.geometry('400x200')
        self.entry = tk.Entry(self.root)
        self.entry.pack()
        self.root.update()
        self.entry.focus_force()
        self.root.update()

    def tearDown(self):
        try:
            self.root.destroy()
        except tk.TclError:
            pass
        self.assertFalse(dialogs._active_interpreters)

    def test_input_blocking_and_grab_focus_restore(self):
        top = tk.Toplevel(self.root)
        top.update()
        top.grab_set()
        top_entry = tk.Entry(top)
        top_entry.pack()
        top_entry.focus_force()
        self.root.update()
        events = []
        original_tags = self.entry.bindtags()
        self.root.bind_all('<KeyPress>', lambda e: events.append('global'))
        self.entry.bind('<ButtonPress>', lambda e: events.append('pointer'))
        with dialogs._TkModal(top) as modal:
            self.assertIsNone(self.root.grab_current())
            self.assertTrue(self.root.tk.call('tk', 'busy', 'status', '.'))
            self.entry.focus_force()
            self.entry.event_generate('<KeyPress-a>')
            self.entry.event_generate('<ButtonPress-1>')
            modal.pump()
            self.assertFalse(events)
        self.assertEqual(self.entry.bindtags(), original_tags)
        self.assertFalse(self.root.tk.call('tk', 'busy', 'status', '.'))
        self.assertEqual(self.root.grab_current(), top)
        self.assertEqual(self.root.focus_get(), top_entry)
        self.entry.event_generate('<ButtonPress-1>')
        self.assertEqual(events, ['pointer'])

    def test_reentry_does_not_disturb_outer_modal(self):
        with dialogs._TkModal(self.root):
            with self.assertRaisesRegex(RuntimeError, 'already active'):
                with dialogs._TkModal(self.root):
                    pass
            self.assertTrue(self.root.tk.call('tk', 'busy', 'status', '.'))

    def test_event_flood_has_a_bounded_pump(self):
        calls = []
        def tick():
            calls.append(1)
            self.root.after(0, tick)
        with dialogs._TkModal(self.root) as modal:
            self.root.after(0, tick)
            start = time.monotonic()
            modal.pump()
            self.assertLess(time.monotonic() - start, .5)
            self.assertGreater(len(calls), 0)
            self.assertLessEqual(len(calls), 64)
        for job in self.root.tk.call('after', 'info'):
            self.root.after_cancel(job)

    def test_new_toplevel_and_existing_busy_state(self):
        self.root.tk.call('tk', 'busy', 'hold', '.')
        with dialogs._TkModal(self.root) as modal:
            top = tk.Toplevel(self.root)
            top.grab_set()
            modal.pump()
            self.assertTrue(self.root.tk.call('tk', 'busy', 'status', str(top)))
            self.assertIsNone(self.root.grab_current())
        self.assertTrue(self.root.tk.call('tk', 'busy', 'status', '.'))
        self.assertEqual(self.root.grab_current(), top)

    def test_owner_destruction_cancels_and_cleans_up(self):
        top = tk.Toplevel(self.root)
        top.update()
        with dialogs._TkModal(top) as modal:
            self.root.after(0, top.destroy)
            self.assertIs(modal.pump(), False)
        self.assertFalse(self.root.tk.call('tk', 'busy', 'status', '.'))
        with dialogs._TkModal(self.root) as modal:
            self.root.after(0, self.root.destroy)
            self.assertIs(modal.pump(), False)

    def test_exception_restores_input(self):
        with self.assertRaisesRegex(ValueError, 'boom'):
            with dialogs._TkModal(self.root):
                raise ValueError('boom')
        self.assertFalse(self.root.tk.call('tk', 'busy', 'status', '.'))
        self.assertFalse(any(tag.startswith('nfd_modal') for tag in self.entry.bindtags()))

    def test_fallback_reuses_explicit_parent(self):
        with patch.object(dialogs, 'resolve_backend', return_value=fallback), \
             patch.object(fallback, 'get_root', side_effect=AssertionError('Extra root')), \
             patch.object(fallback.filedialog, 'askopenfilename', return_value='/tmp/à.pdf') as ask:
            self.assertEqual(dialogs.open_file(master=self.root), ['/tmp/à.pdf'])
        self.assertIs(ask.call_args.kwargs['parent'], self.root)

    def test_non_linux_delegation_does_not_touch_tk(self):
        for platform in ('win32', 'darwin'):
            backend = types.SimpleNamespace(__name__='native_file_dialog.backends.native',
                                            open_file=Mock(return_value=['a']))
            with patch.object(dialogs.sys, 'platform', platform), patch.object(dialogs, 'resolve_backend', return_value=backend):
                self.assertEqual(dialogs.open_file(master=object()), ['a'])
            self.assertNotIn('event_pump', backend.open_file.call_args.kwargs)


if __name__ == '__main__':
    unittest.main()
