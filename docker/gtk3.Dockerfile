ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim-bookworm

RUN apt-get update && apt-get install -y \
    build-essential cmake pkg-config \
    libgtk-3-dev

RUN python -m pip install --upgrade pip && \
    python -m pip install build scikit-build-core

WORKDIR /packages/backend-gtk3
