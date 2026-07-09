"""
CPP Solver Solver - QGIS Plugin

A QGIS plugin to solve the CPP Solver Problem (Route Inspection Problem) for
vector line layers. Finds the shortest closed path that traverses every edge at least once.

Author: Ralf Kistner
Modified for QGIS 4.x and Python 3.9+
"""

from qgis.PyQt.QtCore import QObject, QSettings, QVariant, Qt, pyqtSignal
from qgis.PyQt.QtGui import QIcon, QColor
from qgis.PyQt.QtWidgets import (
    QAction, QMessageBox, QDialog, QVBoxLayout, QHBoxLayout, 
    QLabel, QComboBox, QPushButton, QCheckBox
)
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
from qgis.gui import QgsMapToolEmitPoint
import networkx as nx

from . import cpp_postman as postman
from . import resources


class NodeSelectionTool(QgsMapToolEmitPoint):
    """
    Map tool for selecting nodes by clicking on the map.
    Emits a signal when a node is selected.
    """
    
    node_selected = pyqtSignal(object)  # Emits the selected node (coordinate tuple)
    
    def __init__(self, iface, graph, node_mapping):
        """
        Args:
            iface: QGIS interface.
            graph: NetworkX graph with coordinate tuples as nodes.
            node_mapping: Dict mapping coordinate tuples to human-readable labels.
        """
        super().__init__(iface.mapCanvas())
        self.iface = iface
        self.graph = graph
        self.node_mapping = node_mapping
        self.d = QgsDistanceArea()
        # Tolerance in map units (adjust based on your data)
        # For projected CRS (meters), 10 meters is reasonable
        # For geographic CRS (degrees), 0.0001 degrees (~10 meters) is reasonable
        self.tolerance = 10  # Default tolerance in map units
        
    def set_tolerance(self, tolerance):
        """Set the tolerance for node selection in map units."""
        self.tolerance = tolerance
        
    def canvasReleaseEvent(self, event):
        """
        Called when the user clicks on the map.
        Finds the closest node to the click position.
        Emits node_selected signal if a node is found.
        """
        # Get the clicked point in map coordinates
        point = self.toMapCoordinates(event.pos())
        
        # Find the closest node in the graph
        closest_node = None
        min_distance = float('inf')
        
        for node in self.graph.nodes():
            if isinstance(node, tuple) and len(node) >= 2:
                node_point = QgsPointXY(node[0], node[1])
                try:
                    distance = self.d.measureLine(point, node_point)
                    if distance < min_distance and distance < self.tolerance:
                        min_distance = distance
                        closest_node = node
                except:
                    # Skip nodes that can't be measured (shouldn't happen)
                    pass
        
        if closest_node is not None:
            # Emit the signal with the selected node
            self.node_selected.emit(closest_node)
            # Show a temporary marker (optional)
            self._show_temporary_marker(point)
        else:
            # No node found within tolerance
            QMessageBox.warning(
                None,
                "CPP Solver",
                f"No node found within {self.tolerance} units. Try clicking closer to a node."
            )
    
    def _show_temporary_marker(self, point):
        """Show a temporary marker at the clicked position."""
        # Create a temporary rubber band to show the selection
        # This is optional but provides visual feedback
        pass


class StartEndDialog(QDialog):
    """
    Dialog for selecting start and end nodes for an open path.
    """
    
    def __init__(self, node_labels, parent=None):
        """
        Args:
            node_labels: List of human-readable node labels (e.g., ['Node 1', 'Node 2'])
        """
        super().__init__(parent)
        self.setWindowTitle("Select Start and End Points")
        self.setLayout(QVBoxLayout())
        self.node_labels = node_labels
        
        # Start node selection
        start_layout = QHBoxLayout()
        start_layout.addWidget(QLabel("Start Node:"))
        self.start_combo = QComboBox()
        self.start_combo.addItems(sorted(node_labels))
        start_layout.addWidget(self.start_combo)
        self.layout().addLayout(start_layout)
        
        # End node selection
        end_layout = QHBoxLayout()
        end_layout.addWidget(QLabel("End Node:"))
        self.end_combo = QComboBox()
        self.end_combo.addItems(sorted(node_labels))
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
        """Return the selected start and end node labels."""
        start = self.start_combo.currentText()
        if self.closed_check.isChecked():
            return start, start
        else:
            return start, self.end_combo.currentText()


class CppSolver(QObject):
    """
    QGIS Plugin for solving the CPP Solver Problem.
    """

    def __init__(self, iface):
        """
        Initialize the plugin.

        Args:
            iface: QGIS interface instance.
        """
        super().__init__()
        self.iface = iface
        self.component = None
        self.node_mapping = None
        self.selected_start = None
        self.selected_end = None
        self.selection_tool = None

    def initGui(self):
        """
        Initialize the plugin GUI (add toolbar button and menu item).
        """
        # Create action that will start plugin configuration
        self.action = QAction(
            QIcon(":/plugins/cpp_solver/icon.png"),
            "CPP Solver",
            self.iface.mainWindow()
        )
        # Connect the action to the run method
        self.action.triggered.connect(self.run)

        # Add toolbar button and menu item
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("&CPP Solver", self.action)

    def unload(self):
        """
        Clean up the plugin (remove toolbar button and menu item).
        """
        # Remove the plugin menu item and icon
        self.iface.removePluginMenu("&CPP Solver", self.action)
        self.iface.removeToolBarIcon(self.action)
        
        # Clean up selection tool if it exists
        if self.selection_tool:
            try:
                self.iface.mapCanvas().unsetMapTool(self.selection_tool)
            except:
                pass
            self.selection_tool = None
        
        del self.action

    def _on_node_selected(self, node):
        """
        Called when a node is selected on the map.
        """
        if self.selected_start is None:
            # First selection: start node
            self.selected_start = node
            label = self.node_mapping.get(node, str(node))
            QMessageBox.information(
                None,
                "CPP Solver",
                f"Start node selected: {label}.\nNow click on the END node."
            )
        else:
            # Second selection: end node
            self.selected_end = node
            # Deactivate the tool
            try:
                self.iface.mapCanvas().unsetMapTool(self.selection_tool)
            except:
                pass
            self.selection_tool = None
            
            # Process the selection
            self._process_selection()

    def _process_selection(self):
        """
        Process the selected start and end nodes.
        """
        if self.component is None or self.node_mapping is None:
            QMessageBox.warning(None, "CPP Solver", "Graph data not available.")
            return
        
        try:
            eulerian_graph, nodes = postman.chinese_postman_path_with_start_end(
                self.component, self.selected_start, self.selected_end
            )
            # Map nodes back to labels for display
            nodes = [self.node_mapping.get(node, str(node)) for node in nodes]
        except ValueError as e:
            QMessageBox.warning(None, "CPP Solver", str(e))
            # Fall back to standard path
            eulerian_graph, nodes = postman.single_chinese_postman_path(self.component)
            nodes = [self.node_mapping.get(node, str(node)) for node in nodes]
        
        # Ask if user wants to number the segments
        reply = QMessageBox.question(
            None,
            "CPP Solver",
            "Do you want to number the segments in the output layer?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        number_segments = (reply == QMessageBox.Yes)

        in_length = postman.edge_sum(self.component) / 1000.0
        path_length = postman.edge_sum(eulerian_graph) / 1000.0
        duplicate_length = path_length - in_length

        # Get the CRS from the map canvas
        crs = self.iface.mapCanvas().mapSettings().destinationCrs()
        new_layer = build_layer_with_labels(
            eulerian_graph, nodes, crs, number_segments, self.node_mapping
        )
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

        QMessageBox.information(None, "CPP Solver", info)
        
        # Reset selection
        self.selected_start = None
        self.selected_end = None
        self.component = None
        self.node_mapping = None

    def run(self):
        """
        Main method to execute the plugin logic.
        """
        layer = self.iface.mapCanvas().currentLayer()
        layer_hint = "\n\nPlease select a Vector layer of geometry type Line."

        if layer is None:
            QMessageBox.information(
                None,
                "CPP Solver",
                "No layer selected." + layer_hint
            )
            return

        if layer.type() != QgsMapLayer.VectorLayer:
            QMessageBox.information(
                None,
                "CPP Solver",
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
                "CPP Solver",
                "The selected layer's geometry type is not Line. "
                "CPP Solver cannot work on Point or Polygon." + layer_hint
            )
            return

        features = layer.selectedFeatures()
        if len(features) == 0:
            QMessageBox.information(
                None,
                "CPP Solver",
                "Please select an area. The 'Select Features by Polygon' tool "
                "works well for this."
            )
            return

        # Build graph with human-readable node labels
        graph, node_mapping = build_graph_with_labels(features)
        components = postman.graph_components(graph)
        
        if len(components) > 1:
            QMessageBox.information(
                None,
                "CPP Solver",
                "Warning: the selected area contains multiple disconnected "
                "components - only the largest one will be used."
            )

        if len(components) == 0:
            QMessageBox.information(
                None,
                "CPP Solver",
                "Error: Could not find any components. Try selecting different features."
            )
            return

        component = components[0]
        
        # Store component and mapping for later use
        self.component = component
        self.node_mapping = node_mapping

        # Ask user how they want to select start/end points
        reply = QMessageBox.question(
            None,
            "CPP Solver",
            "How would you like to select start and end points?\n\n"
            "1. Click on the map to select nodes (Recommended)\n"
            "2. Choose from a list of node names",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply == QMessageBox.Yes:
            # Interactive selection on the map
            self._start_interactive_selection()
        else:
            # Use the dialog with node list
            self._start_dialog_selection(component, node_mapping)

    def _start_interactive_selection(self):
        """
        Start the interactive node selection tool.
        """
        # Create and activate the selection tool
        self.selection_tool = NodeSelectionTool(
            self.iface, self.component, self.node_mapping
        )
        self.selection_tool.node_selected.connect(self._on_node_selected)
        
        # Set a reasonable tolerance based on the CRS
        # For now, use a fixed tolerance (can be made configurable later)
        self.selection_tool.set_tolerance(10)  # 10 map units
        
        # Activate the tool
        self.iface.mapCanvas().setMapTool(self.selection_tool)
        
        QMessageBox.information(
            None,
            "CPP Solver",
            "Click on the map to select the START node.\n"
            "Then click again to select the END node.\n\n"
            "If you want a closed circuit, select the same node twice."
        )

    def _start_dialog_selection(self, component, node_mapping):
        """
        Start the dialog-based node selection.
        """
        # Get node labels for the dialog
        node_labels = [label for label in node_mapping.values()]
        if not node_labels:
            QMessageBox.warning(None, "CPP Solver", "No nodes found in the graph.")
            return
        
        dialog = StartEndDialog(node_labels)
        if dialog.exec_() == QDialog.Accepted:
            start_label, end_label = dialog.get_selection()
            
            # Map labels back to actual node identifiers
            start_node = None
            end_node = None
            
            for node, label in node_mapping.items():
                if label == start_label:
                    start_node = node
                    break
            
            for node, label in node_mapping.items():
                if label == end_label:
                    end_node = node
                    break
            
            if start_node is None or end_node is None:
                QMessageBox.warning(None, "CPP Solver", "Could not find selected nodes in graph.")
                return
            
            try:
                eulerian_graph, nodes = postman.chinese_postman_path_with_start_end(
                    component, start_node, end_node
                )
                # Map nodes back to labels for display
                nodes = [node_mapping.get(node, str(node)) for node in nodes]
            except ValueError as e:
                QMessageBox.warning(None, "CPP Solver", str(e))
                # Fall back to standard path
                eulerian_graph, nodes = postman.single_chinese_postman_path(component)
                nodes = [node_mapping.get(node, str(node)) for node in nodes]
            
            # Ask if user wants to number the segments
            reply = QMessageBox.question(
                None,
                "CPP Solver",
                "Do you want to number the segments in the output layer?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            number_segments = (reply == QMessageBox.Yes)

            in_length = postman.edge_sum(component) / 1000.0
            path_length = postman.edge_sum(eulerian_graph) / 1000.0
            duplicate_length = path_length - in_length

            new_layer = build_layer_with_labels(
                eulerian_graph, nodes, layer.crs(), number_segments, node_mapping
            )
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

            QMessageBox.information(None, "CPP Solver", info)
        
        # Reset stored data
        self.component = None
        self.node_mapping = None


def build_graph_with_labels(features):
    """
    Build a NetworkX graph from QGIS features with human-readable node labels.
    
    Args:
        features: List of QgsFeature objects (line features).
    
    Returns:
        Tuple: (graph, node_mapping) where:
            - graph: nx.Graph with coordinate tuples as nodes
            - node_mapping: Dict mapping coordinate tuples to human-readable labels
    """
    d = QgsDistanceArea()
    graph = nx.Graph()
    node_mapping = {}  # Maps (x, y) tuples to human-readable labels
    node_counter = 1
    
    for feature in features:
        geom = feature.geometry()
        geom_single_type = QgsWkbTypes.isSingleType(geom.wkbType())
        
        if geom_single_type:
            # Single part geometry
            nodes = geom.asPolyline()
            for start, end in postman.pairs(nodes):
                length = d.measureLine(start, end)
                start_node = (start.x(), start.y())
                end_node = (end.x(), end.y())
                
                # Add nodes to graph if not already present
                if start_node not in node_mapping:
                    node_mapping[start_node] = f"Node {node_counter}"
                    node_counter += 1
                if end_node not in node_mapping:
                    node_mapping[end_node] = f"Node {node_counter}"
                    node_counter += 1
                
                graph.add_edge(start_node, end_node, weight=length)
        else:
            # Multi-part geometry
            lines = geom.asMultiPolyline()
            for line in lines:
                for start, end in postman.pairs(line):
                    length = d.measureLine(start, end)
                    start_node = (start.x(), start.y())
                    end_node = (end.x(), end.y())
                    
                    # Add nodes to graph if not already present
                    if start_node not in node_mapping:
                        node_mapping[start_node] = f"Node {node_counter}"
                        node_counter += 1
                    if end_node not in node_mapping:
                        node_mapping[end_node] = f"Node {node_counter}"
                        node_counter += 1
                    
                    graph.add_edge(start_node, end_node, weight=length)

    return graph, node_mapping


def build_layer_with_labels(graph, nodes, crs, number_segments=False, node_mapping=None):
    """
    Build a QGIS vector layer from the Eulerian path with human-readable labels.
    
    Args:
        graph: nx.MultiGraph with coordinate tuples as nodes.
        nodes: List of node labels (human-readable) in the path.
        crs: QgsCoordinateReferenceSystem for the layer.
        number_segments: If True, create separate features for each segment with order number.
        node_mapping: Dict mapping coordinate tuples to human-readable labels.
    
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
        
        # Add fields for segment attributes - Use QgsField with type name for QGIS 3.x+
        # QgsField(name, type=QVariant.Int, typeName="integer") is deprecated in favor of QgsField(name, QVariant.Int)
        # But to avoid warnings, we use the new API: QgsField(name, type)
        fields = [
            QgsField("order", QVariant.Int),
            QgsField("start_node", QVariant.String),
            QgsField("end_node", QVariant.String),
            QgsField("length", QVariant.Double),
        ]
        pr.addAttributes(fields)
        vl.updateFields()
        
        # Map labels back to coordinate tuples for path processing
        reverse_mapping = {v: k for k, v in node_mapping.items()} if node_mapping else {}
        coordinate_nodes = []
        for label in nodes:
            if label in reverse_mapping:
                coordinate_nodes.append(reverse_mapping[label])
            else:
                coordinate_nodes.append(label)
        
        # Number the segments and create features
        numbered_edges = postman.number_path_segments(graph, coordinate_nodes)
        for u, v, edge_data, order in numbered_edges:
            # Get coordinates
            if isinstance(u, tuple) and len(u) >= 2:
                start_point = QgsPointXY(u[0], u[1])
                start_label = node_mapping.get(u, str(u))
            else:
                start_point = QgsPointXY(0, 0)
                start_label = str(u)
            
            if isinstance(v, tuple) and len(v) >= 2:
                end_point = QgsPointXY(v[0], v[1])
                end_label = node_mapping.get(v, str(v))
            else:
                end_point = QgsPointXY(0, 0)
                end_label = str(v)
            
            # Create segment geometry
            geometry = QgsGeometry.fromPolylineXY([start_point, end_point])
            fet = QgsFeature()
            fet.setGeometry(geometry)
            
            # Set attributes
            fet.setAttributes([
                order,
                start_label,
                end_label,
                edge_data.get('weight', 0),
            ])
            pr.addFeatures([fet])
    else:
        # Original behavior: single polyline for the entire path
        vl = QgsVectorLayer("LineString", "chinese_postman", "memory")
        vl.setCrs(crs)
        pr = vl.dataProvider()

        # Map labels back to coordinate tuples
        reverse_mapping = {v: k for k, v in node_mapping.items()} if node_mapping else {}
        coordinate_nodes = []
        for label in nodes:
            if label in reverse_mapping:
                coordinate_nodes.append(reverse_mapping[label])
            else:
                coordinate_nodes.append(label)

        # Extract coordinates from the graph nodes
        points = []
        for node in coordinate_nodes:
            if isinstance(node, tuple) and len(node) >= 2:
                points.append(QgsPointXY(node[0], node[1]))
            else:
                points.append(QgsPointXY(0, 0))

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
