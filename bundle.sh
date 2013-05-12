#!/bin/sh
mkdir -p chinesepostman/lib
cp *.py metadata.txt icon.png chinesepostman/
cp lib/*.egg chinesepostman/lib/
zip -r chinesepostman chinesepostman
rm -r chinesepostman

