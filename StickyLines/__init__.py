# -*- coding: utf-8 -*-
"""
/***************************************************************************
 StickyLines
                                 A QGIS plugin
 Redraw lines to follow existing lines of another layer
                             -------------------
        begin                : 2017-08-02
        copyright            : (C) 2017 by Guillaume Silvent
        email                : guillaume.silvent@hotmail.fr
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
    """Load StickyLines class from file StickyLines.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .sticky_lines import StickyLines
    return StickyLines(iface)
