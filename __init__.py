# -*- coding: utf-8 -*-
"""
CPP Solver - QGIS Plugin

This script initializes the plugin, making it known to QGIS.

Author: Ralf Kistner
Modified for QGIS 4.x and Python 3.9+
"""


def classFactory(iface):
    """
    Load CppSolver class from file cpp_solver.

    Args:
        iface: A QGIS interface instance.

    Returns:
        CppSolver: An instance of the plugin class.
    """
    from .cpp_solver import CppSolver
    return CppSolver(iface)
