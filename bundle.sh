#!/bin/sh
# CPP Solver - Bundle Script
# Creates a ZIP file for manual QGIS plugin installation
# Note: The ZIP should contain files directly in the root, not in a subdirectory,
# to avoid the "cpp_solver/cpp_solver" path issue in QGIS.

set -e  # Exit on error

echo "Bundling CPP Solver plugin..."

# Step 1: Compile resources.qrc to resources.py
echo "Compiling resources..."
if command -v pyrcc6 >/dev/null 2>&1; then
    echo "Using pyrcc6 (Qt6)"
    pyrcc6 -o resources.py resources.qrc
elif command -v pyrcc5 >/dev/null 2>&1; then
    echo "Using pyrcc5 (Qt5)"
    pyrcc5 -o resources.py resources.qrc
else
    echo "ERROR: Neither pyrcc5 nor pyrcc6 found."
    echo "Please install PyQt5 or PyQt6 development tools:"
    echo "  - Ubuntu/Debian: sudo apt-get install pyqt5-dev-tools or pyqt6-dev-tools"
    echo "  - Fedora: sudo dnf install python3-qt5-devel or python3-qt6-devel"
    echo "  - macOS: brew install pyqt@5 or pyqt@6"
    exit 1
fi

# Step 2: Create temporary directory for the bundle contents
# We create a flat structure: all files go directly into the temp dir
BUNDLE_DIR="cpp_solver_bundle_contents"
rm -rf "$BUNDLE_DIR"
mkdir -p "$BUNDLE_DIR"

# Step 3: Copy all necessary files (flat structure, no subdirectory)
echo "Copying files..."
cp *.py "$BUNDLE_DIR/"
cp metadata.txt icon.png resources.qrc resources.py "$BUNDLE_DIR/"
cp requirements.txt "$BUNDLE_DIR/"

# Note: We intentionally DO NOT copy the lib/ directory with the old networkx-1.7-py2.7.egg
# because it is incompatible with Python 3.8+ and QGIS 3.x/4.x.
echo "Skipping lib/ directory (old Python 2.7 .egg files are not needed for Python 3.8+)"

# Step 4: Create the ZIP file with files at the root
# This ensures that when extracted, files go directly into the plugin directory
echo "Creating ZIP archive..."
if command -v zip >/dev/null 2>&1; then
    # Change to the temp directory and create ZIP with relative paths
    (cd "$BUNDLE_DIR" && zip -r ../cpp_solver_bundle.zip .)
else
    echo "ERROR: 'zip' command not found."
    echo "Please install zip: sudo apt-get install zip (Ubuntu/Debian)"
    rm -rf "$BUNDLE_DIR"
    exit 1
fi

# Step 5: Clean up
rm -rf "$BUNDLE_DIR"

echo ""
echo "✅ Bundle created: cpp_solver_bundle.zip"
echo ""
echo "IMPORTANT: To install this bundle in QGIS:"
echo "  1. Go to: Plugins -> Manage and Install Plugins... -> Install from ZIP"
echo "  2. Select cpp_solver_bundle.zip"
echo "  3. QGIS will extract the files directly into the plugin directory."
echo ""
echo "NOTE: The bundle does NOT include NetworkX .egg files."
echo "      NetworkX 2.8+ must be installed in your Python environment."
echo "      Install it with: pip install networkx>=2.8"
