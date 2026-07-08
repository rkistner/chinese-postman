#!/bin/sh
# Build chinesepostman.zip for upload to the QGIS plugin repository.
# Note: the top-level folder inside the zip must be named "chinesepostman"
# (a valid Python module name), and plugins.qgis.org requires LICENSE to be
# included in the package.

# Remove the existing zip and temporary folder, create a new temporary folder, copy the
# necessary files into it, create a zip file from that folder, and then remove the temporary folder.
rm -f chinesepostman.zip
rm -rf chinesepostman
mkdir -p chinesepostman
cp *.py metadata.txt icon.png LICENSE Readme.md chinesepostman/
zip -r chinesepostman chinesepostman
rm -r chinesepostman
