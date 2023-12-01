from __future__ import annotations

import enum

from tp.common.qt import api as qt

# Graph Viewer constants
ITEM_CACHE_MODE = qt.QGraphicsItem.DeviceCoordinateCache
# ITEM_CACHE_MODE = QGraphicsItem.ItemCoordinateCache
GRAPH_VIEWER_BACKGROUND_COLOR = (35, 35, 35)			# default background color for the node graph.
GRAPH_VIEWER_GRID_DISPLAY_NONE = 0					    # style node graph background with no grid or dots.
GRAPH_VIEWER_GRID_DISPLAY_DOTS = 1					    # style node graph background with dots.
GRAPH_VIEWER_GRID_DISPLAY_LINES = 2					    # style node graph background with grid lines.
GRAPH_VIEWER_GRID_SIZE = 50							    # grid size when styled with grid lines.
GRAPH_VIEWER_GRID_SPACING = 4						    # grid line spacing.
GRAPH_VIEWER_GRID_COLOR = (60, 60, 60)				    # grid line color.
GRAPH_VIEWER_SECONDARY_GRID_COLOR = (80, 80, 80)		# secondary grid line color.
GRAPH_VIEWER_MINIMUM_ZOOM = -0.8						# minimum view zoom.
GRAPH_VIEWER_MAXIMUM_ZOOM = 2.0						# maximum view zoom.
# GRAPH_VIEWER_MINIMUM_ZOOM = -5.0						# minimum view zoom.
# GRAPH_VIEWER_MAXIMUM_ZOOM = 10.0						# maximum view zoom.

# Node Constants
NODE_MIN_WIDTH = 180
NODE_MIN_HEIGHT = 40
NODE_HEADER_COLOR = (30, 30, 30, 200)
NODE_COLOR = (13, 18, 23, 255)
NODE_SELECTED_COLOR = (255, 255, 255, 30)
NODE_BORDER_COLOR = (74, 84, 85, 255)
NODE_SELECTED_BORDER_COLOR = (38, 187, 255, 255)
NODE_TEXT_COLOR = (255, 255, 255, 180)

# Edge Constants
EDGE_THICKNESS = 2.0
EDGE_COLOR = (170, 95, 30, 255)
EDGE_SLICER_COLOR = (255, 50, 75, 255)
EDGE_DEFAULT_STYLE = qt.Qt.SolidLine
EDGE_DASHED_STYLE = qt.Qt.DashLine
EDGE_DOTTED_STYLE = qt.Qt.DotLine

# Z depth constants
EDGE_Z_VALUE = -1
NODE_Z_VALUE = 1
SOCKET_Z_VALUE = 2
WIDGET_Z_VALUE = 3


class LayoutDirection(enum.IntEnum):
    """
    Node graph nodes layout direction.
    """

    Horizontal = 0          # layout nodes from left to right.
    Vertical = 1            # layout nodes from top to bottom.


class NodePropertyWidget(enum.IntEnum):
    """
    Enumerator used by PropertiesBinWidget to display a node property of the given widget type.
    """

    Hidden = 0
    Label = 1
    LineEdit = 2
    TextEdit = 3
    ComboBox = 4
    CheckBox = 5
    SpinBox = 7
    ColorPicker = 8
    Color4Picker = 9
    Slider = 10
    DoubleSlider = 11
    FileOpen = 12
    FileSave = 13
    Vector2 = 14
    Vector3 = 15
    Vector4 = 16
    Float = 17
    Int = 18
    Button = 19
