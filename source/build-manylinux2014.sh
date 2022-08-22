#!/bin/bash

SOURCE=/cosmonium/source

URL=https://github.com/cosmonium/panda3d/releases/download/
VERSION=1.11.0.dev2716
FULL_VERSION=${VERSION}-ge376654356

PANDA3D_RPM=panda3d-$VERSION.x86_64.rpm
EXTRA_INCLUDES=extra-includes.$VERSION.zip

cd $SOURCE
if [ ! -e $PANDA3D_RPM ]; then
    curl -L $URL/cosmonium-v$FULL_VERSION/$PANDA3D_RPM -o $PANDA3D_RPM
fi
if [ ! -e $EXTRA_INCLUDES ]; then
    curl -L $URL/cosmonium-v$FULL_VERSION/$EXTRA_INCLUDES -o $EXTRA_INCLUDES
fi

PYTHON_DIR=/opt/python/cp37-cp37m
PYTHON_BIN=$PYTHON_DIR/bin
PYTHON_INC=$PYTHON_DIR/include/python3.7m
PYTHON=$PYTHON_BIN/python
PIP=$PYTHON_BIN/pip
CMAKE=$PYTHON_BIN/cmake

yum install -y rpm-build fakeroot
$PIP install cmake

rpm -i --nodeps $SOURCE/$PANDA3D_RPM

cd /usr/include
unzip $SOURCE/$EXTRA_INCLUDES

cd $SOURCE
$PYTHON ../tools/p3d_module_builder/build.py --clean --cmake $CMAKE --python-incdir $PYTHON_INC
