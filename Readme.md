# CPP Solver

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](http://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![NetworkX 2.8+](https://img.shields.io/badge/networkx-2.8+-green.svg)](https://networkx.org/)
[![QGIS 3.0-4.x](https://img.shields.io/badge/qgis-3.0--4.x-brightgreen.svg)](https://qgis.org/)

> **Solves the CPP Solver Problem (Route Inspection Problem)** – Finds the shortest closed path that traverses every edge of a network at least once.

---

## 📖 Table of Contents

- [What is the CPP Solver Problem?](#what-is-the-chinese-postman-problem)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
  - [QGIS Plugin Installation](#qgis-plugin-installation)
  - [Manual Installation](#manual-installation)
  - [Development Setup](#development-setup)
- [Usage](#usage)
  - [Using the QGIS Plugin](#using-the-qgis-plugin)
  - [Command-Line Usage](#command-line-usage)
- [Input/Output Formats](#inputoutput-formats)
  - [CSV Format](#csv-format)
  - [GPX Output](#gpx-output)
  - [PNG Output](#png-output)
- [Algorithm Overview](#algorithm-overview)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## 🤔 What is the CPP Solver Problem?

The **CPP Solver Problem (CPP)**, also known as the **Route Inspection Problem**, is a classic problem in graph theory. The goal is to find the **shortest closed path** that traverses **every edge of a graph at least once**. This is particularly useful for:

- **Route optimization** for delivery services, garbage collection, or street sweeping.
- **Network inspection** (e.g., checking power lines, pipelines).
- **Tour planning** where all roads must be visited.

If the graph is **Eulerian** (all nodes have even degree), the solution is simply an **Eulerian circuit**. Otherwise, some edges must be traversed more than once to make the graph Eulerian.

---

## ✨ Features

- **QGIS Plugin**: Seamless integration with QGIS 3.x and 4.x.
- **Command-Line Tool**: Solve CPP directly from the terminal.
- **Multiple Output Formats**: CSV, GPX (for GPS devices), and PNG (graph visualization).
- **Efficient Algorithm**: Uses the **Blossom algorithm** for optimal pair matching.
- **Handles Disconnected Graphs**: Automatically uses the largest connected component.
- **Open Source**: Licensed under MIT.

---

## 📋 Requirements

### For QGIS Plugin
| Component | Version |
|-----------|---------|
| **QGIS** | 3.0 – 4.x |
| **Python** | 3.8+ |
| **NetworkX** | 2.8+ |

### For Command-Line Usage
| Component | Version | Purpose |
|-----------|---------|---------|
| **Python** | 3.8+ | Core runtime |
| **NetworkX** | 2.8+ | Graph algorithms |
| **Graphviz** | Latest | PNG export (optional) |
| **PyGraphviz** | 1.7+ | PNG export (preferred, optional) |
| **pydot** or **pydotplus** | Latest | PNG export (alternative, optional) |

---

## 💻 Installation

### QGIS Plugin Installation

#### Method 1: Using QGIS Plugin Manager (Recommended)
1. Open QGIS.
2. Go to **Plugins → Manage and Install Plugins...**
3. Search for **"CPP Solver"**.
4. Click **Install Plugin**.
5. The plugin will be available under **Plugins → CPP Solver**.

#### Method 2: Manual Installation from Source
1. Clone this repository:
   ```bash
   git clone https://github.com/pasqal/chinese-postman.git
   cd chinese-postman
   ```
2. Run the installation script:
   ```bash
   ./install.sh
   ```
   This copies the plugin to your QGIS plugins directory.

3. Restart QGIS.

#### Method 3: Bundled Installation
1. Run the bundling script to create a ZIP file:
   ```bash
   ./bundle.sh
   ```
2. In QGIS, go to **Plugins → Manage and Install Plugins... → Install from ZIP**.
3. Select the generated ZIP file.

### Development Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/pasqal/chinese-postman.git
   cd chinese-postman
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run tests:
   ```bash
   python3 postman_test.py
   ```

---

## 🎯 Usage

### Using the QGIS Plugin

#### Step 1: Prepare Your Data
- Load a **vector line layer** (e.g., roads, paths, or any network) into QGIS.
- Ensure the layer has a **valid Coordinate Reference System (CRS)** in meters (e.g., UTM) for accurate distance calculations.

#### Step 2: Select Features
- Use the **"Select Features by Polygon"** tool to select the area of the network you want to analyze.
- Alternatively, select features manually.

#### Step 3: Run the Plugin
1. Go to **Plugins → CPP Solver → CPP Solver**.
2. The plugin will:
   - Analyze the selected features.
   - Compute the optimal CPP Solver path.
   - Create a new **memory layer** named `chinese_postman` with the result.

#### Step 4: Interpret Results
A popup will display:
- **Total length of roads**: Sum of all edge lengths in the input network (in km).
- **Total length of path**: Length of the computed CPP Solver path (in km).
- **Length of sections visited twice**: Extra distance due to duplicated edges (in km).

The result layer will show the **optimal path** as a red line with arrow markers indicating direction.

#### Example Workflow
1. Load a road network layer (e.g., `roads.shp`).
2. Select a subset of roads using the polygon selection tool.
3. Run the plugin.
4. A new layer appears with the optimal inspection route.

---

### Command-Line Usage

#### Basic Usage
```bash
python3 postman.py input.csv
```
This computes and displays the optimal path without saving outputs.

#### Save Outputs
```bash
# Save as CSV and GPX
python3 postman.py --csv output.csv --gpx output.gpx input.csv

# Save as CSV, GPX, and PNG (requires Graphviz)
python3 postman.py --csv output.csv --gpx output.gpx --png output.png input.csv
```

#### Options
| Option | Description | Required |
|--------|-------------|----------|
| `--csv FILE` | Output CSV file with path segments | No |
| `--gpx FILE` | Output GPX file for GPS devices | No |
| `--png FILE` | Output PNG image of the graph | No |
| `input.csv` | Input CSV file (positional argument) | Yes |

#### Example Output
```
Total length of roads: 14.889 km
Total length of path: 20.316 km
Length of sections visited twice: 5.427 km
Node sequence: ['1', '105', '14', '105', '106', ...]
```

---

## 📄 Input/Output Formats

### CSV Format

#### Input CSV
The input CSV file must contain the following **8 columns** (in order):

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| 1 | String/Number | Start node ID | `1` |
| 2 | String/Number | End node ID | `13` |
| 3 | Number | Segment length (meters) | `57.0` |
| 4 | String | Segment name or ID | `Segment 1` |
| 5 | Number | Start longitude | `18.4167` |
| 6 | Number | Start latitude | `-33.9167` |
| 7 | Number | End longitude | `18.6532` |
| 8 | Number | End latitude | `-33.8561` |

**Example:**
```csv
Start Node,End Node,Segment Length,Segment ID,Start Longitude,Start Latitude,End Longitude,End Latitude
1,13,57,Segment 1,18.4167,-33.9167,18.6532,-33.8561
13,22,80,Segment 2,18.6532,-33.8561,18.7650,-33.7930
```

#### Notes:
- The **first row is treated as a header** and is automatically skipped.
- **Segment ID, longitude, and latitude** are used for output but **not for calculations**.
- **Segment length** is used for distance calculations.

#### Output CSV
The output CSV file contains the **optimal path segments** in the same format as the input, but ordered according to the CPP Solver solution.

---

### GPX Output

The GPX file is a standard **GPS Exchange Format** file that can be imported into:
- GPS devices (Garmin, etc.).
- Mapping software (QGIS, Google Earth, etc.).
- Fitness apps (Strava, etc.).

**Features:**
- Contains a single track with the optimal path.
- Each track point includes:
  - Latitude and longitude.
  - Elevation (set to the node ID for reference).

---

### PNG Output

The PNG file is a **graph visualization** of the Eulerian circuit (optimal path).

**Requirements:**
- [Graphviz](https://graphviz.org/) must be installed on your system.
- One of the following Python packages:
  - `pygraphviz` (recommended)
  - `pydot`
  - `pydotplus`

**Installation (Ubuntu/Debian):**
```bash
sudo apt-get install graphviz
pip install pygraphviz
```

---

## 🧮 Algorithm Overview

The plugin uses the following steps to solve the CPP Solver Problem:

1. **Identify Odd-Degree Nodes**: Find all nodes with an odd degree (there will always be an even number of these).
2. **Build Complete Graph of Odd Nodes**: Create a new graph where:
   - Nodes are the odd-degree nodes from the original graph.
   - Edges connect every pair of nodes.
   - Edge weights are the **shortest path distance** between the nodes in the original graph.
3. **Find Optimal Matching**: Use the **Blossom algorithm** (`nx.max_weight_matching`) to find the best pairing of odd nodes (minimizing total added distance).
4. **Duplicate Edges**: For each matched pair, duplicate the shortest path between them in the original graph.
5. **Find Eulerian Circuit**: The modified graph is now Eulerian (all nodes have even degree), so an Eulerian circuit exists and can be found.

**Complexity:**
- If V' (number of odd-degree nodes) is at least 10% of V (total nodes), the complexity is **O(V³)**.

---

## ❓ Troubleshooting

### Common Issues

#### 1. QGIS Plugin Not Appearing
- **Cause**: Plugin not installed correctly or QGIS not restarted.
- **Solution**:
  - Restart QGIS.
  - Check that the plugin is in the correct directory (e.g., `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`).
  - Run `./install.sh` again.

#### 2. Incorrect Distance Calculations
- **Cause**: The layer's **CRS is not in meters** (e.g., WGS84).
- **Solution**:
  - Reproject the layer to a **projected CRS** (e.g., UTM).
  - In QGIS: Right-click the layer → **Export → Save Features As...** → Choose a UTM zone.

#### 3. Plugin Crashes on Large Networks
- **Cause**: The algorithm has **O(V³)** complexity for large graphs.
- **Solution**:
  - Select a smaller subset of the network.
  - Use a more powerful computer.
  - For very large networks, consider using a heuristic approach (not implemented yet).

#### 4. PNG Export Fails
- **Cause**: Graphviz or Python bindings not installed.
- **Solution**:
  - Install Graphviz: `sudo apt-get install graphviz` (Linux) or download from [graphviz.org](https://graphviz.org/).
  - Install Python bindings: `pip install pygraphviz` (recommended) or `pip install pydot`.

#### 5. CSV Import Fails
- **Cause**: Incorrect column order or missing columns.
- **Solution**:
  - Ensure the CSV has **exactly 8 columns** in the correct order.
  - Check that numeric columns (length, coordinates) are valid numbers.

---

## 🤝 Contributing

Contributions are welcome! Here’s how you can help:

1. **Report Bugs**: Open an issue on [GitHub](https://github.com/pasqal/chinese-postman/issues).
2. **Suggest Features**: Open an issue with your feature request.
3. **Submit Code**:
   - Fork the repository.
   - Create a feature branch (`git checkout -b feature/your-feature`).
   - Commit your changes (`git commit -m 'Add some feature'`).
   - Push to the branch (`git push origin feature/your-feature`).
   - Open a Pull Request.

### Development Guidelines
- Follow **PEP 8** for Python code.
- Add **docstrings** to new functions.
- Include **unit tests** for new features.
- Update the **Readme.md** if you change user-facing functionality.

---

## 📜 License

This project is licensed under the **MIT License** – see the [LICENSE](LICENSE) file for details.

```
Copyright (c) 2013-2024 Ralf Kistner and contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
