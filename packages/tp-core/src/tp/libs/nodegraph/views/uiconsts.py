from __future__ import annotations

import enum

from Qt.QtWidgets import QGraphicsItem


# Node graph default background color.
# NODE_GRAPH_BACKGROUND_COLOR = QColor("#393939")
NODE_GRAPH_BACKGROUND_COLOR: tuple[int, int, int] = (35, 35, 35)

# Node graph default grid color.
NODE_GRAPH_GRID_COLOR: tuple[int, int, int] = (55, 55, 55)

# Node graph grid style with no grid or dots.
NODE_GRAPH_GRID_DISPLAY_NONE: int = 0

# Node graph grid style with grid dots.
NODE_GRAPH_GRID_DISPLAY_DOTS: int = 1

# Node graph grid style with grid lines.
NODE_GRAPH_GRID_DISPLAY_LINES: int = 2

# Node graph default grid size.
NODE_GRAPH_GRID_SIZE: int = 50

# Node graph default grid squares.
NODE_GRAPH_GRID_SQUARES: int = 5

# Node graph minimum zoom value.
NODE_GRAPH_MINIMUM_ZOOM = -0.8

# Node graph maximum zoom value.
NODE_GRAPH_MAXIMUM_ZOOM = 2.0

# Node default width.
NODE_WIDTH: int = 100

# Node default height.
NODE_HEIGHT: int = 80

# Node icon default size.
NODE_ICON_SIZE: int = 18

# Default node selected color.
NODE_SELECTED_COLOR: tuple[int, int, int, int] = (255, 255, 255, 30)

# Default node border selected color.
NODE_BORDER_SELECTED_COLOR: tuple[int, int, int, int] = (254, 207, 42, 255)

# Default port size.
PORT_SIZE: float = 22.0

# Default port color.
PORT_COLOR: tuple[int, int, int, int] = (49, 115, 100, 255)

# Default port border color.
PORT_BORDER_COLOR: tuple[int, int, int, int] = (29, 202, 151, 255)

# Default port active color.
PORT_ACTIVE_COLOR: tuple[int, int, int, int] = (14, 45, 59, 255)

# Default port hover color.
PORT_HOVER_COLOR: tuple[int, int, int, int] = (17, 43, 82, 255)

# Default port hover border color.
PORT_HOVER_BORDER_COLOR: tuple[int, int, int, int] = (136, 255, 35, 255)

# Threshold for selecting a port.
PORT_CLICK_FALLOFF: float = 15.0

# Default connector width.
CONNECTOR_WIDTH: float = 1.2

# Default connector color
CONNECTOR_COLOR: tuple[int, int, int, int] = (175, 95, 30, 255)

# Default connector disabled color
CONNECTOR_DISABLED_COLOR: tuple[int, int, int, int] = (200, 60, 60, 255)

# Default connector active color
CONNECTOR_ACTIVE_COLOR: tuple[int, int, int, int] = (70, 255, 220, 255)

# Default connector highlighted color
CONNECTOR_HIGHLIGHTED_COLOR: tuple[int, int, int, int] = (232, 184, 13, 255)

# Connector default thickness.
CONNECTOR_THICKNESS: float = 2.0

# Connector default draw type.
CONNECTOR_DEFAULT_DRAW_TYPE: int = 0

# Connector dashed draw type.
CONNECTOR_DASHED_DRAW_TYPE: int = 1

# Connector dotted draw type.
CONNECTOR_DOTTED_DRAW_TYPE: int = 2

# Default connector slicer color.
CONNECTOR_SLICER_COLOR: tuple[int, int, int, int] = (255, 50, 75, 255)

# Default connector slicer width
CONNECTOR_SLICER_WIDTH: float = 1.5

# Node default item cache mode.
ITEM_CACHE_MODE = QGraphicsItem.DeviceCoordinateCache

# Default Z value for backdrop views.
Z_VALUE_BACKDROP = -2

# Default Z value for connector views.
Z_VALUE_CONNECTOR = -1

# Default Z value for node views.
Z_VALUE_NODE = 1

# Default Z value for port views.
Z_VALUE_PORT = 2

# Default Z value for node widgets.
Z_VALUE_NODE_WIDGET = 3


class ConnectorMode(enum.Enum):
    """
    Enum that defines the different types of connector modes that can be used in a node.
    """

    # Connector is disabled.
    Disabled = 0

    # Connector is being dragged.
    Drag = 2

    # Connector is being cut by slicer.
    Cut = 2

    # Connector is being cut by freehand slicer.
    CutFreehand = 3


class PropertyWidget(enum.Enum):
    """
    Enum that defines the different types of property widgets that can be used in a node.
    """

    # Property will be hidden in the property editor.
    Hidden = 0

    # Node property represented with a ``QLabel`` widget.
    Label = 2

    # Node property represented with a ``QLineEdit`` widget.
    LineEdit = 3

    # Node property represented with a ``QTextEdit`` widget.
    TextEdit = 4

    # Node property represented with a ``QComboBox`` widget.
    ComboBox = 5

    # Node property represented with a ``QCheckBox`` widget.
    CheckBox = 6

    # Node property represented with a ``QSpinBox`` widget.
    SpinBox = 7

    # Node property represented with a ``QDoubleSpinBox`` widget.
    DoubleSpinBox = 8

    # Node property represented with a ColorPicker widget.
    ColorPicker = 9

    # Node property represented with a ColorPicker (RGBA) widget.
    Color4Picker = 10

    # Node property represented with a ``QSlider`` widget.
    Slider = 11

    # Node property represented with a ``QDoubleSlider`` widget.
    DoubleSlider = 12

    # Node property represented with a file selector widget.
    FileOpen = 13

    # Node property represented with a file save widget.
    FileSave = 14

    # Node property represented with a Vector2 widget.
    Vector2 = 15

    # Node property represented with a Vector3 widget.
    Vector3 = 16

    # Node property represented with a Vector4 widget.
    Vector4 = 17

    # Node property represented with a float line edit widget.
    Float = 18

    # Node property represented with an int line edit widget.
    Int = 19

    # Node property represented with a ``QPushButton`` widget.
    Button = 20
