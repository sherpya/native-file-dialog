"""Build optional system-toolkit backends without bundling GTK or Qt.

Run from the backend package directory, inside its Docker build image.
Auditwheel verifies the extension's platform baseline; excluded toolkit
libraries are checked by the core's existing backend selection and fallback.
"""

import argparse
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile


# Only the deliberately external toolkit libraries are excluded. Keep auditwheel's
# checks for the C/C++ runtime, symbol versions and CPU instruction set enabled.
EXTERNAL_LIBRARIES = {
    'gtk': ('libgtk-4.so.1', 'libadwaita-1.so.0', 'libgio-2.0.so.0',
            'libgobject-2.0.so.0', 'libglib-2.0.so.0'),
    'gtk3': ('libgtk-3.so.0', 'libgdk-3.so.0', 'libgio-2.0.so.0',
             'libgobject-2.0.so.0', 'libglib-2.0.so.0'),
    'qt': ('libQt6Core.so.6', 'libQt6Gui.so.6', 'libQt6Widgets.so.6'),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('backend', choices=EXTERNAL_LIBRARIES)
    parser.add_argument('--plat', required=True)
    parser.add_argument('--outdir', type=Path, default=Path('dist'))
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='nfd-wheel-') as temporary:
        staging = Path(temporary)
        subprocess.run([sys.executable, '-m', 'build', '--wheel', '--outdir', str(staging)], check=True)
        wheel, = staging.glob('*.whl')
        repaired = staging / 'repaired'
        command = [sys.executable, '-m', 'auditwheel', 'repair', '--plat', args.plat,
                   '--only-plat', '--wheel-dir', str(repaired)]
        for library in EXTERNAL_LIBRARIES[args.backend]:
            command.extend(['--exclude', library])
        subprocess.run([*command, str(wheel)], check=True)
        result, = repaired.glob('*.whl')
        with zipfile.ZipFile(result) as archive:
            native_files = [name for name in archive.namelist() if '.so' in Path(name).name]
            # Fail rather than accidentally publishing a bundled toolkit or runtime.
            if len(native_files) != 1 or not Path(native_files[0]).name.startswith('_native_'):
                raise RuntimeError(f'Unexpected bundled libraries: {native_files}')
            unpacked = staging / 'import-check'
            archive.extractall(unpacked)
        # Import the actual wheel with the build image's toolkit, not an editable.
        subprocess.run([sys.executable, '-I', '-c',
                        f'import sys; sys.path.insert(0, {str(unpacked)!r}); '
                        f'import native_file_dialog_{args.backend}'], check=True)
        subprocess.run([sys.executable, '-m', 'twine', 'check', '--strict', str(result)], check=True)
        args.outdir.mkdir(parents=True, exist_ok=True)
        destination = args.outdir / result.name
        destination.write_bytes(result.read_bytes())
        print(f'Release wheel: {destination}', flush=True)


if __name__ == '__main__':
    main()
