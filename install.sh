#!/bin/sh
pyrcc5 -o resources.py resources.qrc
ln -sfn $PWD $HOME/.local/share/QGIS/QGIS3/profiles/default/python/plugins/chinesepostman
