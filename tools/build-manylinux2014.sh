#!/bin/bash

cd /app

git config --global --add safe.directory /app

PYTHON_DIR=/opt/python/cp39-cp39
PYTHON_BIN=$PYTHON_DIR/bin
PYTHON_INC=$PYTHON_DIR/include/python3.9
PYTHON=$PYTHON_BIN/python
PIP=$PYTHON_BIN/pip
CMAKE=$PYTHON_BIN/cmake
PLATFORM=manylinux2014_x86_64
SOURCE_OPTIONS="--cmake $CMAKE --python-incdir $PYTHON_INC"

make clean bclean
make PYTHON=$PYTHON PLATFORM=$PLATFORM SOURCE_OPTIONS="$SOURCE_OPTIONS" build
make PYTHON=$PYTHON PLATFORM=$PLATFORM bdist
