ARG PYTHON_VERSION=3.13
FROM python:${PYTHON_VERSION}-slim-trixie

RUN apt-get update && apt-get install -y \
    build-essential cmake pkg-config \
    libgtk-4-dev libadwaita-1-dev

# The official Python image owns /usr/local; no distro Python is modified.
ENV PIP_ROOT_USER_ACTION=ignore

RUN python -m pip install --upgrade pip && \
    python -m pip install build scikit-build-core auditwheel patchelf twine

WORKDIR /packages/backend-gtk
