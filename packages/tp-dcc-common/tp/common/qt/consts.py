#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains constains generic Qt constants
"""

from Qt.QtGui import QColor

# DPI
DEFAULT_DPI = 96

# SPACINGS
SPACING = 2
SMALL_SPACING = 4                       # small widgets spacing (spacing between each sub-widget)
DEFAULT_SPACING = 6                     # default widgets spacing (spacing between each sub-widget)
LARGE_SPACING = 10                      # large spacing of each widget (spacing between each sub-widget)
SUPER_LARGE_SPACING = 15                # very large spacing of each widget (spacing between each sub-widget)
SUPER_LARGE_SPACING_2 = 20              # very large spacing of each widget (spacing between each sub-widget)
SUPER_EXTRA_LARGE_SPACING = 30          # extra large spacing of each widget (spacing between each sub-widget)
WINDOW_SPACING = SPACING

# PADDINGS
TOP_PADDING = 10                        # padding between the top widget and the top frame
BOTTOM_PADDING = 5                      # padding between the bottom widget and bottom of frame.
REGULAR_PADDING = 10                    # padding between widgets
SMALL_PADDING = 5
VERY_SMALL_PADDING = 3
LARGE_PADDING = 15
WINDOW_SIDE_PADDING = 6                 # overall padding for each window side.
WINDOW_TOP_PADDING = 6                  # overall window padding at the top of frame.
WINDOW_BOTTOM_PADDING = 6               # overall window padding at the bottom of frame.
FRAMELESS_VERTICAL_PADDING = 12			# vertical padding for frameless resizers.
FRAMELESS_HORIZONTAL_PADDING = 10		# horizontal padding for frameless resizers.

# MARGINS
MARGINS = (2, 2, 2, 2)                  # default left, top, right, bottom widget margins.
WINDOW_MARGINS = (WINDOW_SIDE_PADDING, WINDOW_BOTTOM_PADDING, WINDOW_SIDE_PADDING, WINDOW_TOP_PADDING)


BUTTON_WIDTH_ICON_MEDIUM = 30

# COLORS
DARK_BG_COLOR = tuple([93, 93, 93])
MEDIUM_DARK_BG_COLOR = tuple([73, 73, 73])

# AXISES
AXISES_COLORS = {
	'x': [255, 0, 0],
	'y': [0, 255, 0],
	'z': [0, 0, 255]
}

# EXTENSIONS
QT_SUPPORTED_EXTENSIONS = ["png", "jpg", "jpeg", "gif", "bmp", "pbm", "pgm", "ppm", "xbm", "xpm"]


class Sizes:
	"""
	Class that contains default sizes that can be used within UIs.
	"""

	TINY = 18
	SMALL = 24
	MEDIUM = 32
	LARGE = 40
	HUGE = 48
	SMALL_FONT_SIZE = 9
	MEDIUM_FONT_SIZE = 10
	LARGE_FONT_SIZE = 14
	MARGIN = 14
	SPACING = 2
	SMALL_SPACING = 4
	MEDIUM_SPACING = 6
	LARGE_SPACING = 10
	VERY_LARGE_SPACING = 15
	HUGE_SPACING = 20
	VERY_HUGE_SPACING = 30
	INDICATOR_WIDTH = 4
	ROW_HEIGHT = 34
	ROW_SEPARATOR = 1
	WIDTH = 640
	HEIGHT = 480
	TITLE_LOGO_ICON = 12
	FRAMELESS_VERTICAL_PADDING = 12
	FRAMELESS_HORIZONTAL_PADDING = 10
	WINDOW_SIDE_PADDING = 6
	WINDOW_BOTTOM_PADDING = 6


class Colors:
	"""
	Class that contains default colors
	"""

	BACKGROUND_COLOR = QColor(75, 75, 78, 255)
	SELECTED_BACKGROUND_COLOR = QColor(140, 140, 140, 255)
	DARK_BACKGROUND_COLOR = QColor(55, 55, 58, 255)
	TEXT = QColor(220, 220, 220, 255)
	SELECTED_TEXT = QColor(250, 250, 250, 255)
	DISABLED_TEXT = QColor(140, 140, 140, 255)
	SECONDARY_TEXT = QColor(170, 170, 170, 255)
	SEPARATOR = QColor(42, 42, 45, 255)
	# BLUE = QColor(107, 135, 165, 255)
	RED = QColor(219, 114, 114, 255)
	GREEN = QColor(90, 200, 155, 255)
	TRANSPARENT_BLACK = QColor(0, 0, 15, 30)
	LOG_BG = QColor(27, 29, 35, 255)
	TRANSPARENT = QColor(0, 0, 0, 0)
	BLUE = QColor('#1890FF')
	PURPLE = QColor('#722ED1')
	CYAN = QColor('#13C2C2')
	# GREEN = '#367F12'
	MAGENTA = QColor('#EB2F96')
	PINK = QColor('#EF5B97')
	# RED = '#F5222D'
	ORANGE = QColor('#FA8C16')
	YELLOW = QColor('#FADB14')
	VOLCANO = QColor('#FA541C')
	GEEK_BLUE = QColor('#2F54EB')
	LIME = QColor('#A0D911')
	GOLD = QColor('#FAAD14')

	@staticmethod
	def rgb(qcolor):
		"""
		Returns the rgba(r, g, b, a) string representation of a QColor.

		:param QColor qcolor: qcolor
		:return: rgba string reprsentation.
		:rtype: str
		"""

		return u'rgba({})'.format(u','.join([str(f) for f in qcolor.getRgb()]))


class ButtonStyles:
	DEFAULT = 0                         # default BaseButton with optional text or an icon.
	TRANSPARENT_BACKGROUND = 1          # default BaseButton with a transparent background.
	ICON_SHADOW = 2						# button with a shadow undelrine.
	DEFAULT_QT = 3                      # default style using standard Qt PushButton.
	ROUNDED = 4                         # rounded button with a background color and a colored icon.
	LABEL_SMALL = 5						# Qt label with a small icon button.
