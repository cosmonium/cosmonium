#!/bin/bash

set -ex

cd /app

git config --global --add safe.directory /app

PYTHON_DIR=/opt/python/cp310-cp310
PYTHON_BIN=$PYTHON_DIR/bin
PYTHON_INC=$PYTHON_DIR/include/python3.10
PYTHON=$PYTHON_BIN/python
PIP=$PYTHON_BIN/pip
PLATFORM=manylinux2014_x86_64
SOURCE_OPTIONS="--python-incdir $PYTHON_INC"

export PATH=$PYTHON_BIN:$PATH

$PIP install -r requirements-dev.txt

make clean bclean
make PYTHON=$PYTHON PLATFORM=$PLATFORM SOURCE_OPTIONS="$SOURCE_OPTIONS" build
make PYTHON=$PYTHON PLATFORM=$PLATFORM bapp
