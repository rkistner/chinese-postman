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
            QMessageBox.information(None, "Chinese Postman", "Please an area. The 'Select Features by Polygon' tool " +
                                                            "works well for this.")
            return

        graph = build_graph(features)
        components = postman.graph_components(graph)
        if len(components) > 1:
            QMessageBox.information(None, "Chinese Postman", "Warning: the selected area contains multiple disconnected " +
                                                             "components - only the largest one will be used.")

        component = components[0]

        eulerian_graph, nodes = postman.single_chinese_postman_path(component)

        in_length = postman.edge_sum(component)/1000.0
        path_length = postman.edge_sum(eulerian_graph)/1000.0
        duplicate_length = path_length - in_length

        info = ""
        info += "Total length of roads: %.3f km\n" % in_length
        info += "Total length of path: %.3f km\n" % path_length
        info += "Length of sections visited twice: %.3f km\n" % duplicate_length

        QMessageBox.information(None, "Chinese Postman", "Done:\n%s" % info)
        newlayer = build_layer(eulerian_graph, nodes, layer.crs())
        QgsMapLayerRegistry.instance().addMapLayer(newlayer)


def set_symbols(layer):
    symbol = QgsSymbolV2.defaultSymbol(layer.geometryType())

    symbol.setColor(QColor('#ff0000'))
    symbol.setAlpha(1)

    layer1 = QgsSimpleLineSymbolLayerV2(QgsSymbolV2.Marker)
    layer1.setColor(QColor('#00ff00'))

    layer2 = QgsSimpleLineSymbolLayerV2(QgsSymbolV2.Line)
    layer2.setColor(QColor('#0000ff'))

    symbol.appendSymbolLayer(layer1)
    symbol.appendSymbolLayer(layer2)

    # marker: {PyQt4.QtCore.QString(u'offset'): PyQt4.QtCore.QString(u'-1'), PyQt4.QtCore.QString(u'interval'): PyQt4.QtCore.QString(u'3'), PyQt4.QtCore.QString(u'rotate'): PyQt4.QtCore.QString(u'1'), PyQt4.QtCore.QString(u'placement'): PyQt4.QtCore.QString(u'interval')}
    # line:   {PyQt4.QtCore.QString(u'color'): PyQt4.QtCore.QString(u'255,238,0,255'), PyQt4.QtCore.QString(u'offset'): PyQt4.QtCore.QString(u'0'), PyQt4.QtCore.QString(u'penstyle'): PyQt4.QtCore.QString(u'solid'), PyQt4.QtCore.QString(u'width'): PyQt4.QtCore.QString(u'0.26'), PyQt4.QtCore.QString(u'use_custom_dash'): PyQt4.QtCore.QString(u'0'), PyQt4.QtCore.QString(u'joinstyle'): PyQt4.QtCore.QString(u'bevel'), PyQt4.QtCore.QString(u'customdash'): PyQt4.QtCore.QString(u'5;2'), PyQt4.QtCore.QString(u'capstyle'): PyQt4.QtCore.QString(u'square')}
    myRenderer = QgsSingleSymbolRendererV2(symbol)
    #myRenderer.setMode(QgsGraduatedSymbolRendererV2.EqualInterval)

    layer.setRendererV2(myRenderer)

def build_layer(graph, nodes, crs):
    # create layer

    # We want to set the CRS without prompting the user, so we disable prompting first
    s = QSettings()
    oldValidation = s.value("/Projections/defaultBehaviour", "useGlobal").toString()
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

    #set_symbols(vl)
    return vl


def build_graph(features):
    graph = nx.Graph()
    for feature in features:
        geom = feature.geometry()
        nodes = geom.asPolyline()
        for start, end in postman.pairs(nodes):
            graph.add_edge((start[0], start[1]), (end[0], end[1]), weight=geom.length())
    return graph

