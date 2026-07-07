"""
Chinese Postman Solver - QGIS Plugin

A QGIS plugin to solve the Chinese Postman Problem (Route Inspection Problem) for
vector line layers. Finds the shortest closed path that traverses every edge at least once.

Author: Ralf Kistner
Modified for QGIS 4.x and Python 3.9+
"""

from qgis.PyQt.QtCore import QObject, QSettings
from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.PyQt.QtGui import QIcon
from qgis.core import (
    QgsWkbTypes,
    QgsApplication,
    QgsProject,
    QgsSymbol,
    QgsSingleSymbolRenderer,
    QgsFeature,
    QgsMapLayer,
    QgsVectorLayer,
    QgsPointXY,
    QgsGeometry,
    QgsDistanceArea,
    QgsSymbolLayerRegistry,
    Qgis,
)
import networkx as nx

from . import postman
from . import resources


class ChinesePostman(QObject):
    """
    QGIS Plugin for solving the Chinese Postman Problem.
    """

    def __init__(self, iface):
        """
        Initialize the plugin.

        Args:
            iface: QGIS interface instance.
        """
        super().__init__()
        self.iface = iface

    def initGui(self):
        """
        Initialize the plugin GUI (add toolbar button and menu item).
        """
        # Create action that will start plugin configuration
        self.action = QAction(
            QIcon(":/plugins/chinesepostman/icon.png"),
            "Chinese Postman",
            self.iface.mainWindow()
        )
        # Connect the action to the run method
        self.action.triggered.connect(self.run)

        # Add toolbar button and menu item
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("&Chinese Postman", self.action)

    def unload(self):
        """
        Clean up the plugin (remove toolbar button and menu item).
        """
        # Remove the plugin menu item and icon
        self.iface.removePluginMenu("&Chinese Postman", self.action)
        self.iface.removeToolBarIcon(self.action)
        del self.action

    def run(self):
        """
        Main method to execute the plugin logic.
        """
        layer = self.iface.mapCanvas().currentLayer()
        layer_hint = "\n\nPlease select a Vector layer of geometry type Line."

        if layer is None:
            QMessageBox.information(
                None,
                "Chinese Postman",
                "No layer selected." + layer_hint
            )
            return

        if layer.type() != QgsMapLayer.VectorLayer:
            QMessageBox.information(
                None,
                "Chinese Postman",
                "The selected layer is not of type Vector." + layer_hint
            )
            return

        # Check for line geometry type (compatible with QGIS 3.x and 4.x)
        # QGIS 4.x uses LineStringGeometry, but also supports LineGeometry for backward compatibility
        geometry_type = layer.geometryType()
        if geometry_type not in (QgsWkbTypes.LineGeometry, QgsWkbTypes.LineStringGeometry):
            QMessageBox.information(
                None,
                "Chinese Postman",
                "The selected layer's geometry type is not Line. "
                "Chinese Postman cannot work on Point or Polygon." + layer_hint
            )
            return

        features = layer.selectedFeatures()
        if len(features) == 0:
            QMessageBox.information(
                None,
                "Chinese Postman",
                "Please select an area. The 'Select Features by Polygon' tool "
                "works well for this."
            )
            return

        graph = build_graph(features)
        components = postman.graph_components(graph)
        
        if len(components) > 1:
            QMessageBox.information(
                None,
                "Chinese Postman",
                "Warning: the selected area contains multiple disconnected "
                "components - only the largest one will be used."
            )

        if len(components) == 0:
            QMessageBox.information(
                None,
                "Chinese Postman",
                "Error: Could not find any components. Try selecting different features."
            )
            return

        component = components[0]

        eulerian_graph, nodes = postman.single_chinese_postman_path(component)

        in_length = postman.edge_sum(component) / 1000.0
        path_length = postman.edge_sum(eulerian_graph) / 1000.0
        duplicate_length = path_length - in_length

        new_layer = build_layer(eulerian_graph, nodes, layer.crs())
        symbol = build_symbol(new_layer)
        new_layer.setRenderer(QgsSingleSymbolRenderer(symbol))
        
        QgsProject.instance().addMapLayer(new_layer)

        info = ""
        info += f"Total length of roads: {in_length:.3f} km\n"
        info += f"Total length of path: {path_length:.3f} km\n"
        info += f"Length of sections visited twice: {duplicate_length:.3f} km\n"
        info += "\n"
        info += "(If the above values do not make sense, consider changing CRS.)\n"

        QMessageBox.information(None, "Chinese Postman", info)


def build_symbol(layer):
    """
    Build a symbol for the result layer (red line with arrow markers).

    Args:
        layer: QgsVectorLayer to style.

    Returns:
        QgsSymbol: Symbol for the layer.
    """
    registry = QgsApplication.symbolLayerRegistry()
    line_meta = registry.symbolLayerMetadata("SimpleLine")
    marker_meta = registry.symbolLayerMetadata("MarkerLine")

    symbol = QgsSymbol.defaultSymbol(layer.geometryType())

    # Line layer (red solid line)
    line_layer = line_meta.createSymbolLayer({
        'width': '0.26',
        'color': '255,0,0',
        'offset': '-1.0',
        'penstyle': 'solid',
        'use_custom_dash': '0',
        'joinstyle': 'bevel',
        'capstyle': 'square'
    })

    # Marker layer (arrow markers along the line)
    marker_layer = marker_meta.createSymbolLayer({
        'width': '0.26',
        'color': '255,0,0',
        'interval': '3',
        'rotate': '1',
        'placement': 'interval',
        'offset': '-1.0'
    })
    sub_symbol = marker_layer.subSymbol()
    # Replace the default layer with a filled arrowhead
    sub_symbol.deleteSymbolLayer(0)
    triangle = registry.symbolLayerMetadata("SimpleMarker").createSymbolLayer({
        'name': 'filled_arrowhead',
        'color': '255,0,0',
        'color_border': '0,0,0',
        'offset': '0,0',
        'size': '1.5',
        'angle': '0'
    })
    sub_symbol.appendSymbolLayer(triangle)

    # Replace the default layer with our two custom layers
    symbol.deleteSymbolLayer(0)
    symbol.appendSymbolLayer(line_layer)
    symbol.appendSymbolLayer(marker_layer)
    
    return symbol


def build_layer(graph, nodes, crs):
    """
    Build a QGIS vector layer from the Eulerian path.

    Args:
        graph: nx.MultiGraph with node coordinates.
        nodes: List of node IDs in the path.
        crs: QgsCoordinateReferenceSystem for the layer.

    Returns:
        QgsVectorLayer: Layer containing the path.
    """
    # Disable CRS prompting to set CRS without user interaction
    s = QSettings()
    old_validation = s.value("/Projections/defaultBehaviour", "useGlobal")
    s.setValue("/Projections/defaultBehaviour", "useGlobal")

    # Create a memory layer for the path
    vl = QgsVectorLayer("LineString", "chinese_postman", "memory")
    vl.setCrs(crs)

    # Restore original CRS behavior
    s.setValue("/Projections/defaultBehaviour", old_validation)

    pr = vl.dataProvider()

    # Extract coordinates from the graph nodes
    points = []
    for node in nodes:
        # Node can be a tuple (x, y) from QGIS geometry or a string ID from CSV
        if isinstance(node, tuple) and len(node) >= 2:
            points.append(QgsPointXY(node[0], node[1]))
        else:
            # For CSV-imported graphs, nodes are string IDs
            node_data = graph.nodes[node]
            lon = node_data.get('longitude', 0)
            lat = node_data.get('latitude', 0)
            points.append(QgsPointXY(lon, lat))

    # Create a polyline feature
    if points:
        # For QGIS 4.x, use fromPolylineXY (compatible with 3.x as well)
        geometry = QgsGeometry.fromPolylineXY(points)
        fet = QgsFeature()
        fet.setGeometry(geometry)
        pr.addFeatures([fet])

    # Update layer's extent
    vl.updateExtents()

    return vl


def build_graph(features):
    """
    Build a NetworkX graph from QGIS features.

    Args:
        features: List of QgsFeature objects (line features).

    Returns:
        nx.Graph: Graph with edges weighted by length.
    """
    d = QgsDistanceArea()
    graph = nx.Graph()
    
    for feature in features:
        geom = feature.geometry()
        geom_single_type = QgsWkbTypes.isSingleType(geom.wkbType())
        
        if geom_single_type:
            # Single part geometry
            nodes = geom.asPolyline()
            for start, end in postman.pairs(nodes):
                length = d.measureLine(start, end)
                graph.add_edge(
                    (start.x(), start.y()),
                    (end.x(), end.y()),
                    weight=length
                )
        else:
            # Multi-part geometry
            lines = geom.asMultiPolyline()
            for line in lines:
                for start, end in postman.pairs(line):
                    length = d.measureLine(start, end)
                    graph.add_edge(
                        (start.x(), start.y()),
                        (end.x(), end.y()),
                        weight=length
                    )

    return graph
