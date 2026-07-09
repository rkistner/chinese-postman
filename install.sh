#!/bin/sh
# CPP Solver - Installation Script
# Modernized for QGIS 3.x and 4.x, Qt5 and Qt6

set -e  # Exit on error

# Step 1: Compile resources using pyrcc5 (Qt5) or pyrcc6 (Qt6)
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

# Step 2: Detect QGIS version and plugin directory
echo "Detecting QGIS installation..."

# Default QGIS profiles directory
QGIS_PROFILES_DIR=""

# Try QGIS 4.x first
if [ -d "$HOME/.local/share/QGIS/QGIS4" ]; then
    QGIS_PROFILES_DIR="$HOME/.local/share/QGIS/QGIS4"
    echo "Detected QGIS 4.x"
elif [ -d "$HOME/.local/share/QGIS/QGIS3" ]; then
    QGIS_PROFILES_DIR="$HOME/.local/share/QGIS/QGIS3"
    echo "Detected QGIS 3.x"
# macOS (Homebrew)
elif [ -d "$HOME/Library/Application Support/QGIS/QGIS4" ]; then
    QGIS_PROFILES_DIR="$HOME/Library/Application Support/QGIS/QGIS4"
    echo "Detected QGIS 4.x (macOS)"
elif [ -d "$HOME/Library/Application Support/QGIS/QGIS3" ]; then
    QGIS_PROFILES_DIR="$HOME/Library/Application Support/QGIS/QGIS3"
    echo "Detected QGIS 3.x (macOS)"
# Windows (OSGeo4W)
elif [ -d "$HOME/AppData/Local/QGIS/QGIS4" ]; then
    QGIS_PROFILES_DIR="$HOME/AppData/Local/QGIS/QGIS4"
    echo "Detected QGIS 4.x (Windows)"
elif [ -d "$HOME/AppData/Local/QGIS/QGIS3" ]; then
    QGIS_PROFILES_DIR="$HOME/AppData/Local/QGIS/QGIS3"
    echo "Detected QGIS 3.x (Windows)"
fi

if [ -z "$QGIS_PROFILES_DIR" ]; then
    echo "ERROR: QGIS installation not found."
    echo "Please install QGIS 3.x or 4.x first."
    exit 1
fi

# Step 3: Find the default profile
DEFAULT_PROFILE="$QGIS_PROFILES_DIR/profiles/default"
if [ ! -d "$DEFAULT_PROFILE" ]; then
    # Try to find any profile
    PROFILES=$(find "$QGIS_PROFILES_DIR/profiles" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | head -n 1)
    if [ -n "$PROFILES" ]; then
        DEFAULT_PROFILE="$PROFILES"
        echo "Using profile: $DEFAULT_PROFILE"
    else
        echo "ERROR: No QGIS profile found in $QGIS_PROFILES_DIR/profiles"
        exit 1
    fi
fi

# Step 4: Create plugins directory if it doesn't exist
PLUGINS_DIR="$DEFAULT_PROFILE/python/plugins/cpp_solver"
echo "Installing to: $PLUGINS_DIR"
mkdir -p "$PLUGINS_DIR"

# Step 5: Create symlink (or copy files)
if [ -L "$PLUGINS_DIR" ]; then
    echo "Removing existing symlink..."
    rm "$PLUGINS_DIR"
fi

ln -sfn "$PWD" "$PLUGINS_DIR"

echo ""
echo "✅ Installation successful!"
echo "Restart QGIS to use the CPP Solver plugin."
echo "The plugin will be available under: Plugins -> CPP Solver"
