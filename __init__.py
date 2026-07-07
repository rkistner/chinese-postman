# -*- coding: utf-8 -*-
"""
Chinese Postman Solver - QGIS Plugin

This script initializes the plugin, making it known to QGIS.

Author: Ralf Kistner
Modified for QGIS 4.x and Python 3.9+
"""


def classFactory(iface):
    """
    Load ChinesePostman class from file ChinesePostman.

    Args:
        iface: A QGIS interface instance.

    Returns:
        ChinesePostman: An instance of the plugin class.
    """
    from .chinesepostman import ChinesePostman
    return ChinesePostman(iface)
