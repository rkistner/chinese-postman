# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ChinesePostman
                                 A QGIS plugin
 Chinese Postman Solver
                             -------------------
        begin                : 2013-05-11
        copyright            : (C) 2013 by Ralf Kistner
        email                : ralf.kistner@gmail.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load ChinesePostman class from file ChinesePostman.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .chinesepostman import ChinesePostman
    return ChinesePostman(iface)
