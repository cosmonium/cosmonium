#!/bin/bash

set -e
set -x

BASEDIR=`pwd`
URL=https://github.com/cosmonium/panda3d/releases/download/
VERSION=1.11.0.dev3844
FULL_VERSION=${VERSION}-g062e3365fd

PANDA3D_RPM=panda3d-$VERSION.x86_64.rpm
EXTRA_INCLUDES=extra-includes.$VERSION.zip

if [ ! -e $PANDA3D_RPM ]; then
    curl -L $URL/cosmonium-v$FULL_VERSION/$PANDA3D_RPM -o $PANDA3D_RPM
fi
if [ ! -e $EXTRA_INCLUDES ]; then
    curl -L $URL/cosmonium-v$FULL_VERSION/$EXTRA_INCLUDES -o $EXTRA_INCLUDES
fi

yum install -y rpm-build fakeroot gettext cmake

rpm -i --nodeps $PANDA3D_RPM

cd /usr/include
unzip $BASEDIR/$EXTRA_INCLUDES
