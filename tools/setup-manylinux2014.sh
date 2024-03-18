#!/bin/bash

set -e
set -x

BASEDIR=`pwd`
URL=https://github.com/cosmonium/panda3d/releases/download/
VERSION=1.11.0.dev3368
FULL_VERSION=${VERSION}-gd9052bae76

PANDA3D_RPM=panda3d-$VERSION.x86_64.rpm
EXTRA_INCLUDES=extra-includes.$VERSION.zip

if [ ! -e $PANDA3D_RPM ]; then
    curl -L $URL/cosmonium-v$FULL_VERSION/$PANDA3D_RPM -o $PANDA3D_RPM
fi
if [ ! -e $EXTRA_INCLUDES ]; then
    curl -L $URL/cosmonium-v$FULL_VERSION/$EXTRA_INCLUDES -o $EXTRA_INCLUDES
fi

PYTHON_DIR=/opt/python/cp39-cp39
PYTHON_BIN=$PYTHON_DIR/bin
PYTHON_INC=$PYTHON_DIR/include/python3.9
PYTHON=$PYTHON_BIN/python
PIP=$PYTHON_BIN/pip
CMAKE=$PYTHON_BIN/cmake

yum install -y rpm-build fakeroot gettext
$PIP install cmake

rpm -i --nodeps $PANDA3D_RPM

cd /usr/include
unzip $BASEDIR/$EXTRA_INCLUDES
