"""
Chinese Postman Solver - QGIS Plugin

A QGIS plugin to solve the Chinese Postman Problem (Route Inspection Problem) for
vector line layers. Finds the shortest closed path that traverses every edge at least once.

Author: Ralf Kistner
Modified for QGIS 4.x and Python 3.9+
"""

from qgis.PyQt.QtCore import QObject, QSettings, QVariant
from qgis.PyQt.QtWidgets import (
    QAction, QMessageBox, QDialog, QVBoxLayout, QHBoxLayout, 
    QLabel, QComboBox, QPushButton, QCheckBox
)
from qgis.PyQt.QtGui import QIcon
from qgis.core import (
    QgsWkbTypes,
    QgsApplication,
    QgsProject,
    QgsSymbol,
    QgsSingleSymbolRenderer,
    QgsFeature,
    QgsField,
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


class StartEndDialog(QDialog):
    """
    Dialog for selecting start and end nodes for an open path.
    """
    
    def __init__(self, nodes, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Start and End Points")
        self.setLayout(QVBoxLayout())
        self.nodes = nodes
        
        # Start node selection
        start_layout = QHBoxLayout()
        start_layout.addWidget(QLabel("Start Node:"))
        self.start_combo = QComboBox()
        self.start_combo.addItems(sorted(nodes))
        start_layout.addWidget(self.start_combo)
        self.layout().addLayout(start_layout)
        
        # End node selection
        end_layout = QHBoxLayout()
        end_layout.addWidget(QLabel("End Node:"))
        self.end_combo = QComboBox()
        self.end_combo.addItems(sorted(nodes))
        end_layout.addWidget(self.end_combo)
        self.layout().addLayout(end_layout)
        
        # Option for closed circuit
        self.closed_check = QCheckBox("Closed circuit (start = end)")
        self.closed_check.stateChanged.connect(self._on_closed_changed)
        self.layout().addWidget(self.closed_check)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        self.layout().addLayout(button_layout)
        
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
    
    def _on_closed_changed(self, state):
        """If closed circuit is checked, disable end node selection."""
        if state == 2:  # Checked
            self.end_combo.setEnabled(False)
        else:
            self.end_combo.setEnabled(True)
    
    def get_selection(self):
        """Return the selected start and end nodes."""
        start = self.start_combo.currentText()
        if self.closed_check.isChecked():
            return start, start
        else:
            return start, self.end_combo.currentText()


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

        # Check for line geometry type
        # QGIS 3.x uses LineGeometry, QGIS 4.x uses LineStringGeometry
        geometry_type = layer.geometryType()
        
        # Get all line geometry types that we support
        line_types = [QgsWkbTypes.LineGeometry]
        
        # Check if LineStringGeometry exists (QGIS 4.x+)
        if hasattr(QgsWkbTypes, 'LineStringGeometry'):
            line_types.append(QgsWkbTypes.LineStringGeometry)
        
        if geometry_type not in line_types:
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

        # Ask user if they want to specify start and end points
        reply = QMessageBox.question(
            None,
            "Chinese Postman",
            "Do you want to specify start and end points for an open path?\n\n"
            "If you select 'Yes', you can choose the start and end nodes.\n"
            "If you select 'No', a closed circuit will be computed.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Get node list for the dialog
            nodes = [str(n) for n in component.nodes()]
            if not nodes:
                QMessageBox.warning(None, "Chinese Postman", "No nodes found in the graph.")
                return
            
            dialog = StartEndDialog(nodes)
            if dialog.exec_() == QDialog.Accepted:
                start_node, end_node = dialog.get_selection()
                try:
                    eulerian_graph, nodes = postman.chinese_postman_path_with_start_end(
                        component, start_node, end_node
                    )
                except ValueError as e:
                    QMessageBox.warning(None, "Chinese Postman", str(e))
                    # Fall back to standard path
                    eulerian_graph, nodes = postman.single_chinese_postman_path(component)
            else:
                return  # User cancelled
        else:
            # Standard closed circuit
            eulerian_graph, nodes = postman.single_chinese_postman_path(component)

        # Ask if user wants to number the segments
        reply = QMessageBox.question(
            None,
            "Chinese Postman",
            "Do you want to number the segments in the output layer?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        number_segments = (reply == QMessageBox.Yes)

        in_length = postman.edge_sum(component) / 1000.0
        path_length = postman.edge_sum(eulerian_graph) / 1000.0
        duplicate_length = path_length - in_length

        new_layer = build_layer(eulerian_graph, nodes, layer.crs(), number_segments)
        symbol = build_symbol(new_layer)
        new_layer.setRenderer(QgsSingleSymbolRenderer(symbol))
        
        QgsProject.instance().addMapLayer(new_layer)

        info = ""
        info += f"Total length of roads: {in_length:.3f} km\n"
        info += f"Total length of path: {path_length:.3f} km\n"
        info += f"Length of sections visited twice: {duplicate_length:.3f} km\n"
        
        if number_segments:
            info += f"Number of segments: {len(nodes) - 1}\n"
            info += "Segments are numbered in the output layer.\n"
        
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


def build_layer(graph, nodes, crs, number_segments=False):
    """
    Build a QGIS vector layer from the Eulerian path.

    Args:
        graph: nx.MultiGraph with node coordinates.
        nodes: List of node IDs in the path.
        crs: QgsCoordinateReferenceSystem for the layer.
        number_segments: If True, create separate features for each segment with order number.

    Returns:
        QgsVectorLayer: Layer containing the path.
    """
    # Disable CRS prompting to set CRS without user interaction
    s = QSettings()
    old_validation = s.value("/Projections/defaultBehaviour", "useGlobal")
    s.setValue("/Projections/defaultBehaviour", "useGlobal")

    if number_segments:
        # Create a layer with separate features for each segment
        vl = QgsVectorLayer("LineString", "chinese_postman", "memory")
        vl.setCrs(crs)
        pr = vl.dataProvider()
        
        # Add fields for segment attributes
        pr.addAttributes([
            QgsField("order", QVariant.Int),
            QgsField("start_node", QVariant.String),
            QgsField("end_node", QVariant.String),
            QgsField("length", QVariant.Double),
            QgsField("segment_id", QVariant.String)
        ])
        vl.updateFields()
        
        # Number the segments and create features
        numbered_edges = postman.number_path_segments(graph, nodes)
        for u, v, edge_data, order in numbered_edges:
            # Get coordinates
            if isinstance(u, tuple) and len(u) >= 2:
                start_point = QgsPointXY(u[0], u[1])
            else:
                node_data = graph.nodes[u]
                start_point = QgsPointXY(node_data.get('longitude', 0), node_data.get('latitude', 0))
            
            if isinstance(v, tuple) and len(v) >= 2:
                end_point = QgsPointXY(v[0], v[1])
            else:
                node_data = graph.nodes[v]
                end_point = QgsPointXY(node_data.get('longitude', 0), node_data.get('latitude', 0))
            
            # Create segment geometry
            geometry = QgsGeometry.fromPolylineXY([start_point, end_point])
            fet = QgsFeature()
            fet.setGeometry(geometry)
            
            # Set attributes
            fet.setAttributes([
                order,
                str(u),
                str(v),
                edge_data.get('weight', 0),
                edge_data.get('id', '')
            ])
            pr.addFeatures([fet])
    else:
        # Original behavior: single polyline for the entire path
        vl = QgsVectorLayer("LineString", "chinese_postman", "memory")
        vl.setCrs(crs)
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
            geometry = QgsGeometry.fromPolylineXY(points)
            fet = QgsFeature()
            fet.setGeometry(geometry)
            pr.addFeatures([fet])

    # Restore original CRS behavior
    s.setValue("/Projections/defaultBehaviour", old_validation)

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
                # Use tuple of coordinates as node identifiers
                start_node = (start.x(), start.y())
                end_node = (end.x(), end.y())
                graph.add_edge(start_node, end_node, weight=length)
        else:
            # Multi-part geometry
            lines = geom.asMultiPolyline()
            for line in lines:
                for start, end in postman.pairs(line):
                    length = d.measureLine(start, end)
                    start_node = (start.x(), start.y())
                    end_node = (end.x(), end.y())
                    graph.add_edge(start_node, end_node, weight=length)

    return graph
