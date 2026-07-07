#!/bin/sh
# Chinese Postman Solver - Bundle Script
# Creates a ZIP file for manual QGIS plugin installation

set -e  # Exit on error

echo "Bundling Chinese Postman Solver plugin..."

# Create temporary directory for the bundle
BUNDLE_DIR="chinesepostman"
rm -rf "$BUNDLE_DIR"
mkdir -p "$BUNDLE_DIR/chinesepostman/lib"

# Copy all necessary files
echo "Copying files..."
cp *.py "$BUNDLE_DIR/chinesepostman/"
cp metadata.txt icon.png resources.qrc "$BUNDLE_DIR/chinesepostman/"
cp requirements.txt "$BUNDLE_DIR/chinesepostman/"

# Copy bundled libraries if they exist
if [ -d "lib" ]; then
    cp lib/*.egg "$BUNDLE_DIR/chinesepostman/lib/" 2>/dev/null || true
fi

# Create the ZIP file
echo "Creating ZIP archive..."
if command -v zip >/dev/null 2>&1; then
    zip -r "$BUNDLE_DIR.zip" "$BUNDLE_DIR"
else
    echo "ERROR: 'zip' command not found."
    echo "Please install zip: sudo apt-get install zip (Ubuntu/Debian)"
    rm -rf "$BUNDLE_DIR"
    exit 1
fi

# Clean up
rm -rf "$BUNDLE_DIR"

echo ""
echo "✅ Bundle created: $BUNDLE_DIR.zip"
echo "You can now install this ZIP file in QGIS via:"
echo "  Plugins -> Manage and Install Plugins... -> Install from ZIP"
