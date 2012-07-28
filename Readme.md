## Chinese postman problem

This is a Python program to solve the [Chinese postman problem](http://en.wikipedia.org/wiki/Route_inspection_problem).

## Requirements

* Python2.7
* [networkx](http://networkx.lanl.gov/)

## Usage

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

## License

Copyright (c) 2012, Ralf Kistner
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
this list of conditions and the following disclaimer in the documentation
and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

