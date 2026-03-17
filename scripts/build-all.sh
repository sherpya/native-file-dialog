#!/bin/bash
# Build all wheels for a given Python version and place them in local-pypi/.
# Usage: ./scripts/build-all.sh <PYTHON_VERSION>
# Example: ./scripts/build-all.sh 3.11
#          ./scripts/build-all.sh 3.13
# Run multiple times with different versions, wheels accumulate.
# Then rsync local-pypi/ to your server.
set -euo pipefail

if [ $# -eq 0 ]; then
    echo "Usage: $0 <PYTHON_VERSION>" >&2
    echo "Example: $0 3.11" >&2
    exit 1
fi

PYVER="$1"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYPI_DIR="$REPO_ROOT/local-pypi"

# --- Build core ---
echo "=== Building core ==="
mkdir -p "$PYPI_DIR/native-file-dialog"
(cd "$REPO_ROOT/packages/core" && python3 -m build --wheel -o "$PYPI_DIR/native-file-dialog")

if [ "${CORE_ONLY:-}" = "1" ]; then
    echo "=== Done (core only) ==="
    exit 0
fi

# --- Build GTK4 ---
echo "=== Building GTK4 (Python $PYVER) ==="
rm -rf "$REPO_ROOT/packages/backend-gtk/dist"
docker build -f "$REPO_ROOT/docker/gtk.Dockerfile" --build-arg PYTHON_VERSION="$PYVER" -t "nfd-gtk:$PYVER" "$REPO_ROOT"
docker run --rm --user "$(id -u):$(id -g)" -v "$REPO_ROOT/packages:/packages" "nfd-gtk:$PYVER" python3 -m build --wheel
mkdir -p "$PYPI_DIR/native-file-dialog-gtk"
cp "$REPO_ROOT/packages/backend-gtk/dist/"*.whl "$PYPI_DIR/native-file-dialog-gtk/"

# --- Build GTK3 ---
echo "=== Building GTK3 (Python $PYVER) ==="
rm -rf "$REPO_ROOT/packages/backend-gtk3/dist"
docker build -f "$REPO_ROOT/docker/gtk3.Dockerfile" --build-arg PYTHON_VERSION="$PYVER" -t "nfd-gtk3:$PYVER" "$REPO_ROOT"
docker run --rm --user "$(id -u):$(id -g)" -v "$REPO_ROOT/packages:/packages" "nfd-gtk3:$PYVER" python3 -m build --wheel
mkdir -p "$PYPI_DIR/native-file-dialog-gtk3"
cp "$REPO_ROOT/packages/backend-gtk3/dist/"*.whl "$PYPI_DIR/native-file-dialog-gtk3/"

# --- Build Qt ---
echo "=== Building Qt (Python $PYVER) ==="
rm -rf "$REPO_ROOT/packages/backend-qt/dist"
docker build -f "$REPO_ROOT/docker/qt.Dockerfile" --build-arg PYTHON_VERSION="$PYVER" -t "nfd-qt:$PYVER" "$REPO_ROOT"
docker run --rm --user "$(id -u):$(id -g)" -v "$REPO_ROOT/packages/backend-qt:/project" "nfd-qt:$PYVER" python3 -m build --wheel
mkdir -p "$PYPI_DIR/native-file-dialog-qt"
cp "$REPO_ROOT/packages/backend-qt/dist/"*.whl "$PYPI_DIR/native-file-dialog-qt/"

echo ""
echo "=== Done (Python $PYVER) ==="
echo "Wheels in $PYPI_DIR/"
find "$PYPI_DIR" -name '*.whl' | sort
