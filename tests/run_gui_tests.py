"""Run GUI regressions on a private X server and D-Bus without desktop services.

From Sigillum: uv run python native-file-dialog/tests/run_gui_tests.py
Requires Xvfb, xauth, dbus-daemon and xdotool. Portals and real multi-monitor
placement are deliberately left to the interactive reproducer.
"""
import os
import signal
from pathlib import Path
import subprocess
import sys
import tempfile


def main():
    tests = Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory(prefix='nfd-tests-') as work:
        config = Path(work) / 'bus.conf'
        config.write_text(f'''<busconfig>
  <type>session</type><listen>unix:tmpdir={work}</listen><auth>EXTERNAL</auth>
  <policy context="default"><allow send_destination="*"/><allow receive_sender="*"/><allow own="*"/></policy>
</busconfig>''')
        bus = subprocess.Popen(['dbus-daemon', '--nofork', '--print-address=1', f'--config-file={config}'],
                               stdout=subprocess.PIPE, text=True)
        try:
            address = bus.stdout.readline().strip()
            if not address:
                raise RuntimeError('Private D-Bus did not start')
            env = {**os.environ, 'DBUS_SESSION_BUS_ADDRESS': address,
                   'XDG_RUNTIME_DIR': work, 'XDG_CACHE_HOME': f'{work}/cache',
                   'XDG_CONFIG_HOME': f'{work}/config', 'XDG_DATA_HOME': f'{work}/data',
                   'XDG_CURRENT_DESKTOP': '', 'XDG_SESSION_DESKTOP': '', 'DESKTOP_SESSION': '', 'KDE_FULL_SESSION': '',
                   'GSETTINGS_BACKEND': 'memory', 'GTK_A11Y': 'none', 'NO_AT_BRIDGE': '1',
                   'GIO_USE_VFS': 'local', 'QT_QPA_PLATFORM': 'xcb', 'QT_QPA_PLATFORMTHEME': '',
                   'QT_STYLE_OVERRIDE': 'Fusion', 'QT_SCALE_FACTOR': '1', 'QT_FONT_DPI': '96'}
            for name in ('GTK_DEBUG', 'WAYLAND_DISPLAY'):
                env.pop(name, None)
            failed = False
            for backend in sys.argv[1:] or ('gtk', 'gtk3', 'qt'):
                print(f'\nTesting {backend}', flush=True)
                env['NFD_TEST_BACKEND'] = backend
                process = subprocess.Popen(['xvfb-run', '-a', sys.executable, '-m', 'unittest',
                                            'discover', '-s', str(tests), '-v'], env=env, start_new_session=True)
                try:
                    failed |= bool(process.wait(timeout=120))
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                    print(f'{backend}: timed out', flush=True)
                    failed = True
            return int(failed)
        finally:
            bus.terminate()
            bus.wait(timeout=5)


if __name__ == '__main__':
    sys.exit(main())
