#!/bin/sh
pyrcc4 -o resources.py  resources.qrc
ln -sfn $PWD $HOME/.qgis/python/plugins/chinesepostman
