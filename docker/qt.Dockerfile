ARG PYTHON_VERSION=3.13
FROM python:${PYTHON_VERSION}-slim-trixie

RUN apt-get update && apt-get install -y \
    python3 python3-dev python3-pip \
    build-essential cmake \
    qt6-base-dev

RUN python -m pip install --upgrade pip && \
    python -m pip install build scikit-build-core pybind11

WORKDIR /project
