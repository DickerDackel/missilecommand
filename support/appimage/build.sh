#!/bin/bash

set -x
set -e

PYTHON_IMAGE=https://github.com/niess/python-appimage/releases/download/python3.14/python3.14.0rc3-cp314-cp314-manylinux2014_x86_64.AppImage

if [ ! -f python.appimage ]; then
    wget -O python.appimage $PYTHON_IMAGE
    chmod 755 python.appimage
fi

if [ ! -d AppDir ]; then
    ./python.appimage --appimage-extract
    mv squashfs-root AppDir
    rm AppDir/AppRun AppDir/python*
    cp support/appimage/* AppDir
fi

cd AppDir
./opt/python3.14/bin/python3.14 -m pip install -U --target missilecommand git+https://github.com/dickerdackel/missilecommand
cd ..
appimagetool AppDir

[ ! -d dist ] && mkdir dist
mv Missile_Command-x86_64.AppImage dist/
