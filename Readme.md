## Chinese postman problem

This is a Python program to solve the [Chinese postman problem](http://en.wikipedia.org/wiki/Route_inspection_problem).

## Installation (QGIS 3.x and 4.x)

QGIS 3.x or 4.x is required for the plugin to run, with
[NetworkX](https://networkx.org/) >= 2.4 available to the QGIS Python
interpreter.

Download the "Chinese Postman Solver", using the QGIS plugin manager.

### Installing NetworkX into QGIS

The plugin runs inside QGIS's own Python interpreter, so NetworkX must be
installed there — installing it into your system Python has no effect. Recent
QGIS 4 builds already bundle NetworkX. To check, run `import networkx` in the
QGIS Python Console (Plugins → Python Console); if it succeeds, you are done.

If it fails, install NetworkX into QGIS's Python and restart QGIS:

* **Any platform**: in the QGIS Python Console, run
  `import pip; pip.main(['install', 'networkx'])`
* **Windows**: alternatively, open the "OSGeo4W Shell" installed alongside
  QGIS and run `python -m pip install networkx`
* **Linux**: alternatively, install your distribution's package, e.g.
  `sudo apt install python3-networkx`

## Manual Installation - Linux / macOS

1. Clone this repository.
2. Run `./install.sh`. This symlinks the repository into the plugin directory
   of every QGIS 3/4 profile found, under the name `chinesepostman`.
3. Restart QGIS and enable "Chinese Postman Solver" in
   Plugins → Manage and Install Plugins → Installed.

Alternatively, run `./bundle.sh` and install the generated `chinesepostman.zip`
via Plugins → Manage and Install Plugins → Install from ZIP. (Do not zip the
repository with the Finder's "Compress" — it adds `__MACOSX` metadata and uses
the repository folder name, neither of which QGIS can load.)

## Usage in QGIS

1. Select the layer for which you want to solve the CPP.
2. Select the features that you want to use. The "Select Features by Polygon" tool works great if you only want to use a small part of a large network.
3. Run Plugins -> Chinese Postman -> Chinese Postman.

It should create a new layer with the results.

## Command-line Usage

Requirements:

* Python 3.x
* [NetworkX](https://networkx.org/)>=2.4
* Optionally, if you want to export PNG images from the command line (not needed for using the QGIS-plugin):
  * [Graphviz](https://graphviz.org/), and
  * [PyGraphviz](https://pygraphviz.github.io/) (preferred) or [pydot](https://github.com/pydot/pydot)


Input data file must be in CSV format, with each row containing the following columns:

* Start node ID
* End node ID
* Segment length in meters
* Segment name or ID
* Start longitude, for example 18.4167
* Start latitude, for example -33.9167
* End longitude
* End latitude

Example:

    Start Node,End Node,Segment Length,Segment ID,Start Longitude,Start Latitude,End Longitude,End Latitude
    1,13,57,Segment 1,18.4167,-33.9167,18.6532,-33.8561
    13,22,80,Segment 2,18.6532,-33.8561,18.7650,-33.7930

Then run (assuming the file is saved as input.csv):

    python postman.py --csv path.csv --gpx path.gpx input.csv


The segment ID and GPS coordinates in the input file are not used for any calculations, but are used for the CSV and GPX
output.

Use option `--png` to create a graph visualization of the route in PNG image format:

    python postman.py --csv path.csv --gpx path.gpx --png path.png input.csv


## Releasing to the QGIS plugin repository

1. Bump `version` and update `changelog` in `metadata.txt`.
2. Run `./bundle.sh` to build `chinesepostman.zip`.
3. Upload the zip at <https://plugins.qgis.org/plugins/> (My Plugins →
   Chinese Postman Solver → Add version).

`metadata.txt` already declares `supportsQt6=True` and
`qgisMaximumVersion=4.99`, so uploaded versions are installable on both
QGIS 3.x and 4.x.

## Contributors

* [Ralf Kistner](https://github.com/rkistner) — author and maintainer
* [Peter Nowee](https://github.com/peternowee)
* [SS7CPhilip](https://github.com/SS7CPhilip)
* [Mike Dezube](https://github.com/mdezube) — QGIS 4 / Qt6 port

## License

All code is licensed under [The MIT License (MIT)](http://opensource.org/licenses/MIT).
