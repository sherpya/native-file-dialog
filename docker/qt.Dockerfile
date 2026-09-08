ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim-bookworm

RUN apt-get update && apt-get install -y \
    python3 python3-dev python3-pip \
    build-essential cmake \
    qt6-base-dev

# The official Python image owns /usr/local; no distro Python is modified.
ENV PIP_ROOT_USER_ACTION=ignore

RUN python -m pip install --upgrade pip && \
    python -m pip install build scikit-build-core auditwheel patchelf twine pybind11

WORKDIR /project
