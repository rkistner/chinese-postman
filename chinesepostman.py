"""
/***************************************************************************
 ChinesePostman
                                 A QGIS plugin
 Chinese Postman Solver
                              -------------------
        begin                : 2013-05-11
        copyright            : (C) 2013 by Ralf Kistner
        email                : ralf.kistner@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

# To reload this plugin after modifying, run:
# qgis.utils.reloadPlugin('chinesepostman')

import postman

# Import the PyQt and QGIS libraries
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
import networkx as nx

# We need to import resources, even though we don't use it directly
import resources

class ChinesePostman:

    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface

    def initGui(self):
        # Create action that will start plugin configuration
        self.action = QAction(QIcon(":/plugins/chinesepostman/icon.png"), \
            "Chinese Postman", self.iface.mainWindow())
        # connect the action to the run method
        QObject.connect(self.action, SIGNAL("triggered()"), self.run)

        # Add toolbar button and menu item
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("&Chinese Postman", self.action)

    def unload(self):
        # Remove the plugin menu item and icon
        self.iface.removePluginMenu("&Chinese Postman",self.action)
        self.iface.removeToolBarIcon(self.action)

    # run method that performs all the real work
    def run(self):
        layer = self.iface.mapCanvas().currentLayer()
        if layer is None:
            QMessageBox.information(None, "Chinese Postman", "Please select a layer.")
            return

        features = layer.selectedFeatures()
        if len(features) == 0:
            QMessageBox.information(None, "Chinese Postman", "Please select an area. The 'Select Features by Polygon' tool " +
                                                            "works well for this.")
            return

        graph = build_graph(features)
        components = postman.graph_components(graph)
        if len(components) > 1:
            QMessageBox.information(None, "Chinese Postman", "Warning: the selected area contains multiple disconnected " +
                                                             "components - only the largest one will be used.")

        if len(components) == 0:
            QMessageBox.information(None, "Chinese Postman", "Error: Could not find any components. Try selecting different features.")
            return

        component = components[0]

        eulerian_graph, nodes = postman.single_chinese_postman_path(component)

        in_length = postman.edge_sum(component)/1000.0
        path_length = postman.edge_sum(eulerian_graph)/1000.0
        duplicate_length = path_length - in_length

        newlayer = build_layer(eulerian_graph, nodes, layer.crs())
        symbol = build_symbol(newlayer)
        newlayer.setRendererV2(QgsSingleSymbolRendererV2(symbol))
        QgsMapLayerRegistry.instance().addMapLayer(newlayer)

        info = ""
        info += "Total length of roads: %.3f km\n" % in_length
        info += "Total length of path: %.3f km\n" % path_length
        info += "Length of sections visited twice: %.3f km\n" % duplicate_length
        info += "\n"
        info += "(If the above values do not make sense, consider changing CRS.)\n"

        QMessageBox.information(None, "Chinese Postman", info)

def build_symbol(layer):
    registry = QgsSymbolLayerV2Registry.instance()
    lineMeta = registry.symbolLayerMetadata("SimpleLine")
    markerMeta = registry.symbolLayerMetadata("MarkerLine")

    symbol = QgsSymbolV2.defaultSymbol(layer.geometryType())

    # Line layer
    lineLayer = lineMeta.createSymbolLayer({'width': '0.26', 'color': '255,0,0', 'offset': '-1.0', 'penstyle': 'solid', 'use_custom_dash': '0', 'joinstyle': 'bevel', 'capstyle': 'square'})

    # Marker layer
    markerLayer = markerMeta.createSymbolLayer({'width': '0.26', 'color': '255,0,0', 'interval': '3', 'rotate': '1', 'placement': 'interval', 'offset': '-1.0'})
    subSymbol = markerLayer.subSymbol()
    # Replace the default layer with our own SimpleMarker
    subSymbol.deleteSymbolLayer(0)
    triangle = registry.symbolLayerMetadata("SimpleMarker").createSymbolLayer({'name': 'filled_arrowhead', 'color': '255,0,0', 'color_border': '0,0,0', 'offset': '0,0', 'size': '1.5', 'angle': '0'})
    subSymbol.appendSymbolLayer(triangle)

    # Replace the default layer with our two custom layers
    symbol.deleteSymbolLayer(0)
    symbol.appendSymbolLayer(lineLayer)
    symbol.appendSymbolLayer(markerLayer)
    
    return symbol


def build_layer(graph, nodes, crs):
    # create layer

    # We want to set the CRS without prompting the user, so we disable prompting first
    s = QSettings()
    oldValidation = s.value("/Projections/defaultBehaviour", "useGlobal")
    s.setValue("/Projections/defaultBehaviour", "useGlobal")

    vl = QgsVectorLayer("LineString", "chinese_postman", "memory")
    vl.setCrs(crs)

    s.setValue("/Projections/defaultBehaviour", oldValidation)

    pr = vl.dataProvider()

    # We use a single polyline to represent the route
    points = []
    for node in nodes:
        points.append(QgsPoint(node[0], node[1]))

    # add the feature
    fet = QgsFeature()
    fet.setGeometry(QgsGeometry.fromPolyline(points))

    pr.addFeatures([fet])

    # update layer's extent when new features have been added
    # because change of extent in provider is not propagated to the layer
    vl.updateExtents()

    return vl


def build_graph(features):
    d = QgsDistanceArea()
    graph = nx.Graph()
    for feature in features:
        geom = feature.geometry()
        nodes = geom.asPolyline()
        for start, end in postman.pairs(nodes):
            graph.add_edge((start[0], start[1]), (end[0], end[1]), weight=d.measureLine(start, end))
    return graph

