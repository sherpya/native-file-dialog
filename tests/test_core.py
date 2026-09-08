import threading
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import native_file_dialog as nfd


class CoreTests(unittest.TestCase):
    def backend(self, name='qt'):
        return types.SimpleNamespace(__name__=f'native_file_dialog.backends.{name}',
                                     open_file=Mock(return_value=['/tmp/caffè.pdf']),
                                     save_file=Mock(return_value='/tmp/caffè.pdf'),
                                     open_directory=Mock(return_value='/tmp'))

    def test_sync_arguments_and_results(self):
        backend = self.backend()
        filters = [('Documenti', '*.pdf;*.p7m')]
        pump = lambda: None
        with patch.object(nfd, 'resolve_backend', return_value=backend), patch.object(nfd.sys, 'platform', 'linux'):
            self.assertEqual(nfd.open_file('Apri', Path('/tmp'), filters, True, event_pump=pump), ['/tmp/caffè.pdf'])
            backend.open_file.assert_called_once_with(title='Apri', initialdir='/tmp', filters=filters,
                                                      multiple=True, event_pump=pump)
            self.assertEqual(nfd.save_file(default_name='caffè.pdf', event_pump=pump), '/tmp/caffè.pdf')
            self.assertEqual(backend.save_file.call_args.kwargs['default_name'], 'caffè.pdf')
            self.assertEqual(nfd.open_directory(event_pump=pump), '/tmp')

    def test_legacy_calls_do_not_forward_new_argument(self):
        backend = self.backend()
        with patch.object(nfd, 'resolve_backend', return_value=backend):
            nfd.open_file()
        self.assertNotIn('event_pump', backend.open_file.call_args.kwargs)

    def test_non_linux_and_tk_keep_their_own_wait(self):
        for platform, name in [('win32', 'win32'), ('darwin', 'pyobjc'), ('linux', 'tk')]:
            with self.subTest(platform=platform):
                backend = self.backend(name)
                pump = Mock(side_effect=AssertionError('Unexpected pump'))
                with patch.object(nfd, 'resolve_backend', return_value=backend), patch.object(nfd.sys, 'platform', platform):
                    nfd.open_file(event_pump=pump)
                self.assertNotIn('event_pump', backend.open_file.call_args.kwargs)
                pump.assert_not_called()

    def test_reentry_and_error_release_guard(self):
        backend = self.backend()
        backend.open_file.side_effect = lambda **kw: nfd.save_file()
        with patch.object(nfd, 'resolve_backend', return_value=backend), patch.object(nfd.sys, 'platform', 'linux'):
            with self.assertRaisesRegex(RuntimeError, 'already active'):
                nfd.open_file()
            backend.save_file.assert_not_called()
            backend.open_file.side_effect = ValueError('native failure')
            with self.assertRaisesRegex(ValueError, 'native failure'):
                nfd.open_file()
            backend.open_file.side_effect = None
            self.assertTrue(nfd.open_file())

    def test_worker_thread_rejected_before_backend_call(self):
        backend = self.backend()
        errors = []
        def run():
            try:
                nfd.open_file()
            except RuntimeError as error:
                errors.append(str(error))
        with patch.object(nfd, 'resolve_backend', return_value=backend), patch.object(nfd.sys, 'platform', 'linux'):
            worker = threading.Thread(target=run)
            worker.start()
            worker.join(2)
        self.assertEqual(len(errors), 1)
        self.assertIn('main thread', errors[0])
        backend.open_file.assert_not_called()


if __name__ == '__main__':
    unittest.main()
