#!/bin/sh
pyrcc4 -o resources.py  resources.qrc
ln -sfn $PWD $HOME/.qgis2/python/plugins/chinesepostman
