#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains constant definitions used by Node Graph library
"""

from Qt.QtCore import Qt
from Qt.QtWidgets import QGraphicsItem

URI_SCHEME = 'nodegraph://'
URN_SCHEME = 'nodegraph::'

ITEM_CACHE_MODE = QGraphicsItem.DeviceCoordinateCache
# ITEM_CACHE_MODE = QGraphicsItem.ItemCoordinateCache
NODE_LAYOUT_VERTICAL = 0
NODE_LAYOUT_HORIZONTAL = 1
NODE_LAYOUT_DIRECTION = NODE_LAYOUT_HORIZONTAL

NODE_CATEGORY = 'Default'
NODE_KEYWORDS = list()
NODE_DESCRIPTION = 'Default node description'
NODE_WIDTH = 150
NODE_HEIGHT = 80
NODE_ICON_NAME = 'tpDcc'
NODE_ICON_SIZE = 24
NODE_SELECTED_COLOR = (255, 255, 255, 30)
NODE_SELECTED_BORDER_COLOR = (38, 187, 255, 255)
NODE_HEADER_COLOR = (30, 30, 30, 200)
NODE_COLOR = (13, 18, 23, 255)
NODE_BORDER_COLOR = (74, 84, 85, 255)
NODE_TEXT_COLOR = (255, 255, 255, 180)

SOCKET_FALLOFF = 15.0
SOCKET_DEFAULT_SIZE = 22
SOCKET_SIZE = 22
SOCKET_OFFSET = 15
SOCKET_DEFAULT_COLOR = (49, 115, 100, 255)
SOCKET_DEFAULT_BORDER_COLOR = (29, 202, 151, 255)
SOCKET_ACTIVE_COLOR = (14, 45, 59, 255)
SOCKET_ACTIVE_BORDER_COLOR = (107, 166, 193, 255)
SOCKET_HOVER_COLOR = (17, 43, 82, 255)
SOCKET_HOVER_BORDER_COLOR = (136, 255, 35, 255)

CONNECTOR_THICKNESS = 1
CONNECTOR_COLOR = (170, 95, 30, 255)
CONNECTOR_SLICER_COLOR = (255, 50, 75, 255)

# Z depth constants
CONNECTOR_Z_VALUE = -1
NODE_Z_VALUE = 1
SOCKET_Z_VALUE = 2
WIDGET_Z_VALUE = 3


class NodeGraphViewStyle(object):
	"""
	Node graph viewer styling layout
	"""

	BACKGROUND_COLOR = (35, 35, 35)			# default background color for the node graph.
	GRID_DISPLAY_NONE = 0					# style node graph background with no grid or dots.
	GRID_DISPLAY_DOTS = 1					# style node graph background with dots.
	GRID_DISPLAY_LINES = 2					# style node graph background with grid lines.
	GRID_SIZE = 50							# grid size when styled with grid lines.
	GRID_SPACING = 4						# grid line spacing.
	GRID_COLOR = (60, 60, 60)				# grid line color.
	SECONDARY_GRID_COLOR = (80, 80, 80)		# secondary grid line color.
	MINIMUM_ZOOM = -0.8						# minimum view zoom.
	MAXIMUM_ZOOM = 2.0						# maximum view zoom.


class NodeGraphViewNavStyle(object):
	BACKGROUND_COLOR = (25, 25, 25)			# default background color.
	ITEM_COLOR = (35, 35, 35)				# default item color.


class SocketDirection(object):
	"""
	Defines the available socket directions
	"""

	Input = 'in'                   # input socket direction
	Output = 'out'                 # output socket direction


class ConnectorStyles(object):
	"""
	Defines the available connector draw styles.
	"""

	DEFAULT = Qt.SolidLine
	DASHED = Qt.DashLine
	DOTTED = Qt.DotLine

	@staticmethod
	def get(connector_style):
		return {
			ConnectorStyles.DEFAULT: Qt.SolidLine,
			ConnectorStyles.DASHED: Qt.DashLine,
			ConnectorStyles.DOTTED: Qt.DotLine
		}.get(connector_style)


class ConnectorLayoutStyles(object):
	"""
	Defines the available connector layout styles.
	"""

	STRAIGHT = 0
	CURVED = 1
	ANGLE = 2


class GraphLayoutDirection(object):
	"""
	Defines the available graph layout directions.
	"""

	HORIZONTAL = 0
	VERTICAL = 1


class PropertiesEditorWidgets(object):
	"""
	Defines all available properties editor widgets
	"""

	HIDDEN = 0                 # property type will hidden in the properties editor (default).
	LABEL = 2                   # property type represented with a QLabel widget in the properties editor.
	LINE_EDIT = 3               # property type represented with a QLineEdit widget in the properties editor.
	TEXT_EDIT = 4               # property type represented with a QTextEdit widget in the properties editor.
	COMBOBOX = 5                # property type represented with a QComboBox widget in the properties editor.
	CHECKBOX = 6                # property type represented with a QCheckBox widget in the properties editor.
	SPINBOX = 7                 # property type represented with a QSpinBox widget in the properties editor.
	DOUBLE_SPINBOX = 8          # property type represented with a QDoubleSpinBox widget in the properties editor.
	COLOR_PICKER = 9            # property type represented with a ColorPicker widget in the properties editor.
	SLIDER = 10                 # property type represented with a Slider widget in the properties editor.
	FILE = 11                   # property type represented with a file selector widget in the properties editor.
	FILE_SAVE = 12              # property type represented with a file save widget in the properties editor.
	VECTOR2 = 13                # property type represented with a vector2 widget in the properties editor.
	VECTOR3 = 14                # property type represented with vector3 widget in the properties editor.
	VECTOR4 = 15                # property type represented with vector4 widget in the properties editor.
	FLOAT = 16                  # property type represented with float widget in the properties editor.
	INT = 17                    # property type represented with int widget in the properties editor.
	BUTTON = 18                 # property type represented with button widget in the properties editor.
