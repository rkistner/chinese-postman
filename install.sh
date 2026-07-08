#!/bin/sh
# Link this repository into the plugin directory of every QGIS 3/4 profile
# found (Linux and macOS locations).
for base in "$HOME/.local/share/QGIS/QGIS3" \
            "$HOME/.local/share/QGIS/QGIS4" \
            "$HOME/Library/Application Support/QGIS/QGIS3" \
            "$HOME/Library/Application Support/QGIS/QGIS4"; do
    for profile in "$base"/profiles/*/; do
        [ -d "$profile" ] || continue
        plugins="${profile}python/plugins"
        mkdir -p "$plugins"
        ln -sfn "$PWD" "$plugins/chinesepostman"
        echo "Linked into $plugins"
    done
done
